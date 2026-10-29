import json
import logging
import re
import time
from datetime import date
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

_status_cache: dict[str, Any] | None = None
_status_checked_at = 0.0
_cloud_call_count = 0
_cloud_call_day = date.today()


def _active_provider() -> str:
    if settings.llm_provider == "auto":
        return "openai_compatible" if settings.llm_api_key else "ollama"
    return settings.llm_provider


def _provider_name(provider: str) -> str:
    if provider == "openai_compatible":
        return settings.llm_provider_label.strip() or "openai_compatible"
    return provider


def _provider_model(provider: str) -> str:
    if provider == "ollama":
        return settings.ollama_model
    if provider == "openai_compatible":
        return settings.llm_model
    return ""


def _provider_base_url(provider: str) -> str:
    if provider == "ollama":
        return settings.ollama_base_url
    if provider == "openai_compatible":
        return settings.llm_base_url
    return ""


def _meta(
    provider: str,
    used: bool,
    latency_ms: int,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "provider": _provider_name(provider),
        "model": _provider_model(provider),
        "used": used,
        "latency_ms": latency_ms,
        "error": error,
    }


def fallback_meta(reason: str) -> dict[str, Any]:
    return _meta(_active_provider(), False, 0, reason)


def _reserve_cloud_call() -> bool:
    global _cloud_call_count, _cloud_call_day

    today = date.today()
    if today != _cloud_call_day:
        _cloud_call_day = today
        _cloud_call_count = 0

    limit = settings.llm_daily_request_limit
    if limit > 0 and _cloud_call_count >= limit:
        return False
    _cloud_call_count += 1
    return True


def _parse_json(content: str) -> dict[str, Any] | None:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


async def _chat_ollama(
    system: str,
    prompt: str,
    *,
    json_mode: bool,
    max_tokens: int | None,
) -> tuple[str | None, dict[str, Any]]:
    payload: dict[str, Any] = {
        "model": settings.ollama_model,
        "stream": False,
        "keep_alive": "10m",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "options": {
            "temperature": settings.llm_temperature,
            "num_predict": max_tokens or settings.llm_max_tokens,
            "num_ctx": settings.llm_context_tokens,
        },
    }
    if json_mode:
        payload["format"] = "json"

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        content = ((data.get("message") or {}).get("content") or "").strip()
        latency_ms = int((time.perf_counter() - started) * 1000)
        if not content:
            logger.warning("llm_empty_response provider=ollama model=%s", settings.ollama_model)
            return None, _meta("ollama", False, latency_ms, "empty_response")
        logger.info(
            "llm_response provider=ollama model=%s latency_ms=%s characters=%s",
            settings.ollama_model,
            latency_ms,
            len(content),
        )
        return content, _meta("ollama", True, latency_ms)
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.warning(
            "llm_request_failed provider=ollama model=%s latency_ms=%s error=%s",
            settings.ollama_model,
            latency_ms,
            type(exc).__name__,
        )
        return None, _meta("ollama", False, latency_ms, type(exc).__name__)


async def _chat_openai_compatible(
    system: str,
    prompt: str,
    *,
    json_mode: bool,
    max_tokens: int | None,
) -> tuple[str | None, dict[str, Any]]:
    if not settings.llm_api_key:
        return None, _meta("openai_compatible", False, 0, "missing_api_key")
    if not _reserve_cloud_call():
        logger.warning("llm_daily_limit provider=%s", _provider_name("openai_compatible"))
        return None, _meta("openai_compatible", False, 0, "daily_limit")

    payload: dict[str, Any] = {
        "model": settings.llm_model,
        "stream": False,
        "temperature": settings.llm_temperature,
        "max_tokens": max_tokens or settings.llm_max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    if json_mode and settings.llm_json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    started = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            if response.status_code == 429:
                latency_ms = int((time.perf_counter() - started) * 1000)
                logger.warning("llm_rate_limited provider=%s", _provider_name("openai_compatible"))
                return None, _meta("openai_compatible", False, latency_ms, "rate_limited")
            if response.status_code in (401, 403):
                latency_ms = int((time.perf_counter() - started) * 1000)
                logger.warning(
                    "llm_unauthorized provider=%s status=%s",
                    _provider_name("openai_compatible"),
                    response.status_code,
                )
                return None, _meta("openai_compatible", False, latency_ms, "unauthorized")
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices")
        message = choices[0].get("message") if isinstance(choices, list) and choices else {}
        content = (message.get("content") or "").strip() if isinstance(message, dict) else ""
        latency_ms = int((time.perf_counter() - started) * 1000)
        if not content:
            logger.warning(
                "llm_empty_response provider=%s model=%s",
                _provider_name("openai_compatible"),
                settings.llm_model,
            )
            return None, _meta("openai_compatible", False, latency_ms, "empty_response")
        logger.info(
            "llm_response provider=%s model=%s latency_ms=%s characters=%s",
            _provider_name("openai_compatible"),
            settings.llm_model,
            latency_ms,
            len(content),
        )
        return content, _meta("openai_compatible", True, latency_ms)
    except httpx.TimeoutException:
        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.warning(
            "llm_request_failed provider=%s model=%s latency_ms=%s error=timeout",
            _provider_name("openai_compatible"),
            settings.llm_model,
            latency_ms,
        )
        return None, _meta("openai_compatible", False, latency_ms, "timeout")
    except httpx.HTTPStatusError as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        error = "http_error"
        if exc.response.status_code == 400:
            error = "bad_request"
        logger.warning(
            "llm_request_failed provider=%s model=%s latency_ms=%s status=%s",
            _provider_name("openai_compatible"),
            settings.llm_model,
            latency_ms,
            exc.response.status_code,
        )
        return None, _meta("openai_compatible", False, latency_ms, error)
    except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.warning(
            "llm_request_failed provider=%s model=%s latency_ms=%s error=%s",
            _provider_name("openai_compatible"),
            settings.llm_model,
            latency_ms,
            type(exc).__name__,
        )
        return None, _meta("openai_compatible", False, latency_ms, type(exc).__name__)


async def _chat(
    system: str,
    prompt: str,
    *,
    json_mode: bool,
    max_tokens: int | None,
) -> tuple[str | None, dict[str, Any]]:
    provider = _active_provider()
    if provider == "disabled":
        return None, _meta(provider, False, 0, "disabled")
    if provider == "openai_compatible" and not settings.llm_api_key:
        return None, _meta(provider, False, 0, "missing_api_key")
    if provider == "ollama":
        return await _chat_ollama(
            system,
            prompt,
            json_mode=json_mode,
            max_tokens=max_tokens,
        )
    return await _chat_openai_compatible(
        system,
        prompt,
        json_mode=json_mode,
        max_tokens=max_tokens,
    )


async def complete_json(
    system: str,
    prompt: str,
    *,
    max_tokens: int | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    content, meta = await _chat(
        system,
        prompt,
        json_mode=True,
        max_tokens=max_tokens,
    )
    if content is None:
        return None, meta

    parsed = _parse_json(content)
    if parsed is None:
        logger.warning("llm_invalid_json provider=%s", meta.get("provider"))
        return None, {**meta, "used": False, "error": "invalid_json"}
    return parsed, meta


async def complete_text(
    system: str,
    prompt: str,
    *,
    max_tokens: int | None = None,
) -> tuple[str | None, dict[str, Any]]:
    content, meta = await _chat(
        system,
        prompt,
        json_mode=False,
        max_tokens=max_tokens,
    )
    if content is None:
        return None, meta
    cleaned = content.strip().strip("`").strip()
    return cleaned or None, meta


async def _status_uncached() -> dict[str, Any]:
    provider = _active_provider()
    info: dict[str, Any] = {
        "enabled": settings.llm_enabled,
        "provider": _provider_name(provider),
        "model": _provider_model(provider),
        "base_url": _provider_base_url(provider),
        "reachable": False,
        "model_available": False,
        "models": [],
    }

    if provider == "disabled":
        info["enabled"] = False
        info["error"] = "disabled"
        return info
    if provider == "openai_compatible" and not settings.llm_api_key:
        info["enabled"] = False
        info["error"] = "missing_api_key"
        return info

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            if provider == "ollama":
                response = await client.get(
                    f"{settings.ollama_base_url.rstrip('/')}/api/tags"
                )
                response.raise_for_status()
                data = response.json()
                models = [
                    item.get("name", "")
                    for item in (data.get("models") or [])
                    if isinstance(item, dict)
                ]
            else:
                response = await client.get(
                    f"{settings.llm_base_url.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                )
                response.raise_for_status()
                data = response.json()
                models = [
                    item.get("id", "")
                    for item in (data.get("data") or [])
                    if isinstance(item, dict)
                ]
    except (httpx.HTTPError, ValueError):
        return info

    target = _provider_model(provider)
    info["reachable"] = True
    info["models"] = [model for model in models if model]
    info["model_available"] = target in info["models"]
    return info


async def status() -> dict[str, Any]:
    global _status_cache, _status_checked_at

    if (
        _status_cache is not None
        and _status_cache.get("reachable")
        and settings.llm_status_cache_seconds > 0
        and (time.monotonic() - _status_checked_at) < settings.llm_status_cache_seconds
    ):
        return _status_cache

    info = await _status_uncached()
    if info.get("reachable"):
        _status_cache = info
        _status_checked_at = time.monotonic()
    return info
