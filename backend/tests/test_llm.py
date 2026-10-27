import asyncio

from app.agents import _clean_cover, _clean_feedback, _clean_score, orchestrator
from app.providers.llm import _parse_json, complete_json, status


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
    assert info["model"] == "qwen2.5-coder:7b"


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
