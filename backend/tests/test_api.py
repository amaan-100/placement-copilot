import uuid


def _upload(client, headers, sample_pdf):
    response = client.post(
        "/api/resume/upload",
        headers=headers,
        files={"file": ("resume.pdf", sample_pdf, "application/pdf")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_health_and_session_headers(client, headers):
    response = client.get("/api/health", headers=headers)
    assert response.status_code == 200
    assert response.json()["approval_gate"] is True
    assert response.headers["X-Session-Id"] == headers["X-Session-Id"]
    assert response.headers.get("X-Request-ID")


def test_happy_path_upload_search_draft_approve(client, headers, sample_pdf):
    uploaded = _upload(client, headers, sample_pdf)
    assert uploaded["resume_id"] > 0
    assert "python" in uploaded["facts"]["skills"]
    assert "raw_text" not in uploaded["facts"]

    latest = client.get("/api/resume/latest", headers=headers)
    assert latest.status_code == 200
    assert latest.json()["id"] == uploaded["resume_id"]

    search = client.post(
        "/api/jobs/search",
        headers=headers,
        json={"query": "cybersecurity internship"},
    )
    assert search.status_code == 200, search.text
    payload = search.json()
    assert payload["source"] == "mock_fallback"
    assert payload["cached"] is False
    assert payload["jobs"]
    job = payload["jobs"][0]
    assert job["id"] > 0
    assert job["match_score"] >= 0

    cached = client.post(
        "/api/jobs/search",
        headers=headers,
        json={"query": "cybersecurity internship"},
    )
    assert cached.status_code == 200
    assert cached.json()["cached"] is True
    assert cached.json()["jobs"][0]["id"] == job["id"]

    draft = client.post(
        "/api/applications/draft",
        headers=headers,
        json={"job_id": job["id"]},
    )
    assert draft.status_code == 201, draft.text
    drafted = draft.json()
    assert drafted["status"] == "PENDING_APPROVAL"
    assert drafted["cover_note"]
    assert drafted["resume_draft"]

    application_id = drafted["application_id"]
    approve = client.post(
        f"/api/applications/{application_id}/approve",
        headers=headers,
    )
    assert approve.status_code == 200, approve.text
    assert approve.json()["status"] == "APPROVED"

    repeated = client.post(
        f"/api/applications/{application_id}/approve",
        headers=headers,
    )
    assert repeated.status_code == 200
    assert repeated.json()["status"] == "APPROVED"
    assert "already" in repeated.json()["message"].lower()

    applications = client.get("/api/applications", headers=headers)
    assert applications.status_code == 200
    assert len(applications.json()["applications"]) == 1
    assert applications.json()["applications"][0]["status"] == "APPROVED"

    dashboard = client.get("/api/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json() == {
        "applications": 1,
        "pending_approvals": 0,
        "interviews": 0,
        "approved": 1,
    }

    traces = client.get("/api/traces", headers=headers)
    assert traces.status_code == 200
    trace_agents = {trace["agent"] for trace in traces.json()}
    assert {"resume", "job", "document"}.issubset(trace_agents)


def test_interview_flow(client, headers):
    started = client.post(
        "/api/interviews",
        headers=headers,
        json={"goal": "cybersecurity internship"},
    )
    assert started.status_code == 201, started.text
    interview_id = started.json()["interview_id"]
    assert started.json()["question"]

    evaluated = client.post(
        f"/api/interviews/{interview_id}/evaluate",
        headers=headers,
        json={
            "interview_id": interview_id,
            "answer": (
                "I would first contain the incident because evidence can be lost quickly. "
                "For example, I would isolate the host, capture logs, test my hypothesis, "
                "monitor for lateral movement, and document risk before we mitigate."
            ),
        },
    )
    assert evaluated.status_code == 200, evaluated.text
    assert evaluated.json()["score"] >= 80
    assert evaluated.json()["status"] == "EVALUATED"


def test_sessions_are_isolated(client, sample_pdf):
    first = {"X-Session-Id": str(uuid.uuid4())}
    second = {"X-Session-Id": str(uuid.uuid4())}

    _upload(client, first, sample_pdf)
    assert client.get("/api/resume/latest", headers=first).status_code == 200
    assert client.get("/api/resume/latest", headers=second).status_code == 404
    assert client.get("/api/dashboard", headers=second).json()["applications"] == 0


def test_rejects_non_pdf_and_bad_magic(client, headers):
    wrong_type = client.post(
        "/api/resume/upload",
        headers=headers,
        files={"file": ("resume.txt", b"hello", "text/plain")},
    )
    assert wrong_type.status_code == 400
    assert wrong_type.json()["error"]["code"] == "invalid_file_type"

    bad_magic = client.post(
        "/api/resume/upload",
        headers=headers,
        files={"file": ("resume.pdf", b"not a pdf", "application/pdf")},
    )
    assert bad_magic.status_code == 422
    assert bad_magic.json()["error"]["code"] == "invalid_pdf"


def test_validation_and_unknown_job_errors(client, headers, sample_pdf):
    invalid = client.post(
        "/api/jobs/search",
        headers=headers,
        json={"query": "x"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "validation_error"

    _upload(client, headers, sample_pdf)
    missing_job = client.post(
        "/api/applications/draft",
        headers=headers,
        json={"job_id": 999999},
    )
    assert missing_job.status_code == 404
    assert missing_job.json()["error"]["code"] == "job_not_found"
