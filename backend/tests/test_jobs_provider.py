from app.providers.jobs import _normalize_live_job, _select_jobs, _unique_skills


def test_skills_are_normalized_and_deduplicated():
    assert _unique_skills(["Python", "python", " ", "SQL", "Sql"]) == ["python", "sql"]


def test_live_job_normalization_strips_html_noise():
    job = {
        "id": 7,
        "jobTitle": "Security Operations Analyst",
        "companyName": "Huntress",
        "jobGeo": "USA",
        "url": "https://example.com/jobs/7",
        "jobIndustry": ["Cybersecurity", "cybersecurity"],
        "jobDescription": (
            "<p style='font-variant:normal;font-style:normal'>"
            "Python and SQL. JavaScript is a plus."
            "</p>"
        ),
    }

    normalized = _normalize_live_job(job)

    assert normalized["external_id"] == "7"
    assert normalized["skills"][0] == "cybersecurity"
    assert {"python", "sql", "javascript"}.issubset(normalized["skills"])
    assert "font" not in normalized["skills"]
    assert "normal" not in normalized["skills"]
    assert len(normalized["skills"]) == len(set(normalized["skills"]))


def test_live_job_selection_keeps_query_matches():
    jobs = [
        {
            "title": "AI Trainer",
            "company": "iMerit",
            "skills": ["video"],
            "raw": {"jobDescription": "<p>AI training work.</p>"},
        },
        {
            "title": "Security Operations Analyst",
            "company": "Huntress",
            "skills": ["cybersecurity"],
            "raw": {},
        },
        {
            "title": "Python Developer",
            "company": "BuildStack",
            "skills": ["python"],
            "raw": {},
        },
        {
            "title": "Cybersecurity Intern",
            "company": "SecureNet",
            "skills": ["security"],
            "raw": {},
        },
    ]

    selected = _select_jobs(jobs, "cybersecurity internship")
    titles = [job["title"] for job in selected]

    assert titles[0] == "Cybersecurity Intern"
    assert "Security Operations Analyst" in titles
    assert "AI Trainer" not in titles
