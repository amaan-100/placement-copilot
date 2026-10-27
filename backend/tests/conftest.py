import os
import tempfile
import uuid
from pathlib import Path

TEST_DIR = Path(tempfile.mkdtemp(prefix="placement-test-"))

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_DIR / 'test.db').as_posix()}"
os.environ["JOBS_PROVIDER"] = "mock"
os.environ["LLM_PROVIDER"] = "disabled"
os.environ["RATE_LIMIT_REQUESTS"] = "10000"
os.environ["RATE_LIMIT_UPLOAD_REQUESTS"] = "10000"
os.environ["LOG_LEVEL"] = "WARNING"

import fitz  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def session_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def headers(session_id: str) -> dict[str, str]:
    return {"X-Session-Id": session_id}


@pytest.fixture
def sample_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Test Candidate\n"
        "Skills: Python, SQL, Linux, Networking, React\n"
        "Experience: Built a Flask API and analyzed network logs for a SOC project.",
    )
    data = doc.tobytes()
    doc.close()
    return data
