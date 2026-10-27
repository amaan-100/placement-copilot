import json
import logging
import re
import time
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


def _meta(used: bool, latency_ms: int, error: str | None = None) -> dict[str, Any]:
    return {
        "provider": "ollama",
        "model": settings.ollama_model,
        "used": used,
        "latency_ms": latency_ms,
        "error": error,
    }


def fallback_meta(reason: str) -> dict[str, Any]:
    return _meta(False, 0, reason)


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


async def _chat(
    system: str,
    prompt: str,
    *,
    json_mode: bool,
    max_tokens: int | None,
) -> tuple[str | None, dict[str, Any]]:
    if not settings.llm_enabled:
        return None, fallback_meta("disabled")

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
            logger.warning("llm_empty_response model=%s", settings.ollama_model)
            return None, _meta(False, latency_ms, "empty_response")
        logger.info(
            "llm_response model=%s latency_ms=%s characters=%s",
            settings.ollama_model,
            latency_ms,
            len(content),
        )
        return content, _meta(True, latency_ms)
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.warning(
            "llm_request_failed model=%s latency_ms=%s error=%s",
            settings.ollama_model,
            latency_ms,
            type(exc).__name__,
        )
        return None, _meta(False, latency_ms, type(exc).__name__)


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
        logger.warning("llm_invalid_json model=%s", settings.ollama_model)
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


async def status() -> dict[str, Any]:
    info: dict[str, Any] = {
        "enabled": settings.llm_enabled,
        "provider": "ollama",
        "model": settings.ollama_model,
        "base_url": settings.ollama_base_url,
        "reachable": False,
        "model_available": False,
        "models": [],
    }
    if not settings.llm_enabled:
        return info

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                f"{settings.ollama_base_url.rstrip('/')}/api/tags"
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError):
        return info

    models = [
        item.get("name", "")
        for item in (data.get("models") or [])
        if isinstance(item, dict)
    ]
    target = settings.ollama_model
    info["reachable"] = True
    info["models"] = models
    info["model_available"] = target in models or any(
        name.split(":")[0] == target.split(":")[0] for name in models
    )
    return info
