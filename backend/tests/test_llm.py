import asyncio
from datetime import date

from app.agents import _clean_cover, _clean_feedback, _clean_score, orchestrator
from app.config import settings
from app.providers import llm
from app.providers.llm import _parse_json, complete_json, complete_text, status


def test_parse_json_handles_code_fences_and_extra_text():
    assert _parse_json('{"score": 80, "feedback": "ok"}') == {
        "score": 80,
        "feedback": "ok",
    }
    assert _parse_json('```json\n{"score": 70}\n```') == {"score": 70}
    assert _parse_json('Result: {"score": 60} done') == {"score": 60}
    assert _parse_json("not json") is None


def test_disabled_llm_falls_back_to_deterministic_agents():
    facts, meta = asyncio.run(orchestrator.resume.analyze("Python and SQL project"))
    assert "python" in facts["skills"]
    assert meta["used"] is False
    assert meta["error"] == "disabled"

    _, cover, cover_meta = asyncio.run(
        orchestrator.docs.draft(
            "Python and SQL project",
            {"title": "Developer", "company": "Acme", "skills": ["python"]},
        )
    )
    assert "Acme" in cover
    assert cover_meta["used"] is False

    question, question_meta = asyncio.run(
        orchestrator.interview.question("cybersecurity internship")
    )
    assert len(question) > 15
    assert question_meta["used"] is False

    score, feedback, evaluate_meta = asyncio.run(
        orchestrator.interview.evaluate(
            "cybersecurity internship",
            question,
            (
                "I would contain the incident because evidence can be lost quickly. "
                "For example, I would isolate the host, capture logs, test my "
                "hypothesis, monitor for lateral movement, and document risk."
            ),
        )
    )
    assert 0 <= score <= 100
    assert feedback
    assert evaluate_meta["used"] is False


def test_disabled_llm_returns_no_generation():
    payload, meta = asyncio.run(complete_json("system", "prompt"))
    assert payload is None
    assert meta["used"] is False

    info = asyncio.run(status())
    assert info["enabled"] is False
    assert info["provider"] == "disabled"
    assert info["model"] == ""


def test_auto_provider_prefers_cloud_when_key_is_present(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "auto")
    monkeypatch.setattr(settings, "llm_api_key", "")
    assert llm._active_provider() == "ollama"

    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    assert llm._active_provider() == "openai_compatible"


def test_cloud_daily_cap_reserves_calls(monkeypatch):
    monkeypatch.setattr(llm, "_cloud_call_count", 0)
    monkeypatch.setattr(llm, "_cloud_call_day", date.today())
    monkeypatch.setattr(settings, "llm_daily_request_limit", 1)

    assert llm._reserve_cloud_call() is True
    assert llm._reserve_cloud_call() is False


def test_openai_compatible_provider_uses_cloud_contract(monkeypatch):
    calls: list[dict] = []

    class FakeResponse:
        status_code = 200

        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            return None

        def json(self):
            return self._data

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            calls.append({"url": url, "headers": headers, "json": json})
            if json and json.get("response_format"):
                return FakeResponse({"choices": [{"message": {"content": '{"ok": true}'}}]})
            return FakeResponse({"choices": [{"message": {"content": "Generated cover"}}]})

        async def get(self, url, headers=None):
            calls.append({"url": url, "headers": headers})
            return FakeResponse({"data": [{"id": "test/model"}]})

    monkeypatch.setattr(llm.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "llm_provider", "openai_compatible")
    monkeypatch.setattr(settings, "llm_provider_label", "requesty")
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_base_url", "https://example.test/v1")
    monkeypatch.setattr(settings, "llm_model", "test/model")
    monkeypatch.setattr(settings, "llm_json_mode", True)

    content, meta = asyncio.run(complete_text("system", "prompt"))
    assert content == "Generated cover"
    assert meta["provider"] == "requesty"
    assert meta["model"] == "test/model"
    assert meta["used"] is True
    assert calls[0]["url"] == "https://example.test/v1/chat/completions"
    assert calls[0]["headers"]["Authorization"] == "Bearer test-key"

    payload, json_meta = asyncio.run(complete_json("system", "prompt"))
    assert payload == {"ok": True}
    assert json_meta["used"] is True
    assert calls[1]["json"]["response_format"] == {"type": "json_object"}

    info = asyncio.run(status())
    assert info["provider"] == "requesty"
    assert info["reachable"] is True
    assert info["model_available"] is True
    assert info["models"] == ["test/model"]


def test_openai_compatible_provider_requires_key(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai_compatible")
    monkeypatch.setattr(settings, "llm_provider_label", "requesty")
    monkeypatch.setattr(settings, "llm_api_key", "")

    content, meta = asyncio.run(complete_text("system", "prompt"))
    assert content is None
    assert meta["used"] is False
    assert meta["error"] == "missing_api_key"
    assert meta["provider"] == "requesty"


def test_cover_guard_rejects_unsupported_claims():
    resume = (
        "Amaan Candidate\nSkills: Python, Linux\n"
        "Experience: Built a Flask API and analyzed network logs."
    )
    grounded = (
        "Dear Hiring Team,\n\nI built a Flask API and analyzed network logs "
        "using Python and Linux. I would welcome the chance to discuss the role."
        "\n\nSincerely,\nAmaan Candidate"
    )
    assert _clean_cover(grounded, resume) == grounded
    assert _clean_cover(
        "Dear Hiring Team,\n\nI have over 4 years of experience in a SOC role.",
        resume,
    ) is None
    assert _clean_cover(
        "Dear Hiring Team,\n\nIn my previous role I led a security team.",
        resume,
    ) is None
    assert _clean_cover("I have 4 years of experience.", resume) is None


def test_llm_output_normalization_accepts_common_shapes():
    assert _clean_score("45/100") == 45
    assert _clean_score("82") == 82
    assert _clean_feedback(["First concrete point.", "Second concrete point."]) == (
        "First concrete point. Second concrete point."
    )
