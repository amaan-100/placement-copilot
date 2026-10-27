import html
import json
import re
from pathlib import Path

import fitz

BASE = Path(__file__).resolve().parents[1]
MAX_PDF_PAGES = 30

SKILL_VOCABULARY = [
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "react",
    "next.js",
    "vue",
    "angular",
    "node.js",
    "flask",
    "django",
    "fastapi",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "redis",
    "linux",
    "kali",
    "networking",
    "cybersecurity",
    "security",
    "information security",
    "git",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "terraform",
    "ansible",
    "siem",
    "splunk",
    "burp suite",
    "wireshark",
    "nmap",
    "metasploit",
    "owasp",
    "penetration testing",
    "incident response",
    "threat hunting",
    "firewall",
    "tcp/ip",
    "dns",
    "http",
    "bash",
    "powershell",
    "html",
    "css",
    "tailwind",
    "graphql",
    "rest",
    "ci/cd",
    "jenkins",
    "github actions",
    "pandas",
    "numpy",
    "tensorflow",
    "pytorch",
    "machine learning",
    "data analysis",
    "agile",
    "jira",
    "excel",
    "tableau",
    "power bi",
    "figma",
    "ui/ux",
    "seo",
    "content writing",
    "copywriting",
    "editing",
    "social media",
    "video editing",
    "customer service",
    "sales",
    "accounting",
    "bookkeeping",
    "project management",
    "product management",
    "communication",
    "leadership",
]

_SKILL_PATTERNS = [
    (skill, re.compile(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])"))
    for skill in SKILL_VOCABULARY
]

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def html_to_text(value: str) -> str:
    return SPACE_RE.sub(" ", html.unescape(TAG_RE.sub(" ", value or ""))).strip()


def extract_skills(text: str) -> list[str]:
    low = (text or "").lower()
    found: list[str] = []
    for skill, pattern in _SKILL_PATTERNS:
        if pattern.search(low):
            found.append(skill)
    return found


def extract_pdf(path: str) -> str:
    doc = fitz.open(path)
    try:
        if doc.needs_pass:
            raise ValueError("Encrypted PDFs are not supported.")
        if doc.page_count > MAX_PDF_PAGES:
            raise ValueError(f"PDF has too many pages (max {MAX_PDF_PAGES}).")
        return "\n".join(page.get_text() for page in doc).strip()
    finally:
        doc.close()


def resume_facts(text: str) -> dict:
    return {"skills": extract_skills(text), "raw_text": text}


def local_jobs() -> list[dict]:
    return json.loads((BASE / "data/mock_jobs.json").read_text(encoding="utf-8"))


def rank_jobs(jobs: list[dict], skills: list[str], goal: str) -> list[dict]:
    words = set(re.findall(r"[a-zA-Z0-9+#.-]{3,}", goal.lower()))
    ranked = []
    for job in jobs:
        text = " ".join(
            [
                job.get("title", ""),
                job.get("company", ""),
                " ".join(job.get("skills", [])),
            ]
        ).lower()
        skill_hits = sum(1 for skill in skills if skill.lower() in text)
        goal_hits = sum(1 for word in words if word in text)
        ranked.append({**job, "match_score": min(100, skill_hits * 15 + goal_hits * 8)})
    return sorted(ranked, key=lambda item: item["match_score"], reverse=True)


def deterministic_document(resume_text: str, job: dict) -> tuple[str, str]:
    skills = resume_facts(resume_text)["skills"]
    relevant = [skill for skill in skills if skill in " ".join(job.get("skills", [])).lower()]
    cover = (
        f"Dear Hiring Team,\n\nI am interested in the {job['title']} opportunity at "
        f"{job['company']}. My background includes skills already present in my resume: "
        f"{', '.join(relevant or skills[:6]) or 'the experience described in my resume'}.\n\n"
        "I would welcome the opportunity to discuss how my existing experience can "
        "contribute to the role.\n\nRegards,\nCandidate"
    )
    return resume_text, cover


def interview_question(goal: str) -> str:
    bank = [
        "Explain a security incident you would investigate first in a SOC and why.",
        "How would you identify whether a suspicious network connection is malicious?",
        "Tell me about a technical project you built and one challenge you solved.",
        "What is the difference between authentication and authorization?",
        "How would you safely investigate a phishing email?",
    ]
    return bank[sum(map(ord, goal or "")) % len(bank)]


def evaluate_answer(answer: str) -> tuple[int, str]:
    words = len(answer.split())
    terms = [
        "because",
        "example",
        "approach",
        "test",
        "risk",
        "monitor",
        "evidence",
        "mitigate",
    ]
    hits = sum(term in answer.lower() for term in terms)
    score = min(100, 35 + min(words, 40) + hits * 6)
    feedback = (
        "Good structure. Add a concrete example and explain your reasoning."
        if words >= 25
        else "Answer is too short. Give context, your approach, evidence, and outcome."
    )
    if score >= 80:
        feedback = (
            "Strong answer. Keep the reasoning concrete and connect it to measurable "
            "outcomes where your resume supports them."
        )
    return score, feedback
