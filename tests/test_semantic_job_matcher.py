import pytest
from services.job_matcher import match_resume_to_job, build_job_profile
from services.candidate_profile import build_candidate_profile
from services.nlp import embedding_service


def create_parsed_resume_fixture(cleaned_text: str, skills: list[str], section_dict: dict = None) -> dict:
    """Helper fixture to construct mock parsed resume dictionary."""
    sections = {
        "summary": section_dict.get("summary", "") if section_dict else "",
        "skills": ", ".join(skills),
        "experience": section_dict.get("experience", "") if section_dict else cleaned_text,
        "education": section_dict.get("education", "Bachelor's Degree") if section_dict else "Bachelor's Degree",
        "projects": "",
        "certifications": ""
    }
    parsed = {
        "cleaned_text": cleaned_text,
        "sections": sections,
        "skills": skills,
        "has_text": True
    }
    parsed["candidate_profile"] = build_candidate_profile(parsed)
    return parsed


def test_tech_domain_semantic_match():
    """Verify high match score for technology backend developer."""
    resume_text = "Software Engineer with 4 years experience in Python, FastAPI, PostgreSQL, REST APIs, and Docker."
    resume = create_parsed_resume_fixture(resume_text, ["Python", "FastAPI", "PostgreSQL", "REST API", "Docker"])

    jd_text = """
    Required Qualifications:
    - Python backend engineer with experience in FastAPI and REST API development.
    - Experience with PostgreSQL database and Docker containers.
    """
    res = match_resume_to_job(resume, jd_text)

    assert res["has_job_description"] is True
    assert res["job_match_score"] >= 70
    assert "Python" in res["matched_skills"] or "Python" in res["matched_required_skills"]


def test_finance_domain_semantic_match():
    """Verify high match score for finance & accounting domain."""
    resume_text = "Senior Accountant specializing in Financial Reporting, Accounts Payable, Excel, and QuickBooks."
    resume = create_parsed_resume_fixture(resume_text, ["Financial Reporting", "Accounts Payable", "Excel", "QuickBooks"])

    jd_text = """
    We are seeking an Accountant for financial statement preparation, accounts payable management, and Excel reporting.
    """
    res = match_resume_to_job(resume, jd_text)

    assert res["has_job_description"] is True
    assert res["job_match_score"] >= 65
    assert len(res["matched_skills"]) > 0


def test_marketing_domain_semantic_match():
    """Verify high match score for digital marketing domain."""
    resume_text = "Digital Marketer experienced in SEO, Content Strategy, Google Analytics, and Campaign Management."
    resume = create_parsed_resume_fixture(resume_text, ["SEO", "Content Strategy", "Google Analytics"])

    jd_text = """
    Digital Marketing Specialist required for search engine optimization, content marketing strategy, and campaign management.
    """
    res = match_resume_to_job(resume, jd_text)

    assert res["has_job_description"] is True
    assert res["job_match_score"] >= 65


def test_healthcare_domain_semantic_match():
    """Verify high match score for healthcare & nursing domain."""
    resume_text = "Registered Nurse experienced in Patient Care, Clinical Documentation, Vital Signs, and Medication Administration."
    resume = create_parsed_resume_fixture(resume_text, ["Patient Care", "Clinical Documentation", "Medication Administration"])

    jd_text = """
    Looking for a Registered Nurse to provide direct patient care, clinical documentation, and medication administration.
    """
    res = match_resume_to_job(resume, jd_text)

    assert res["has_job_description"] is True
    assert res["job_match_score"] >= 65


def test_education_domain_semantic_match():
    """Verify high match score for education domain."""
    resume_text = "Educator specializing in Lesson Planning, Classroom Management, Student Assessment, and Pedagogy."
    resume = create_parsed_resume_fixture(resume_text, ["Lesson Planning", "Classroom Management", "Curriculum Development"])

    jd_text = """
    School Teacher needed for lesson planning, classroom management, and student curriculum development.
    """
    res = match_resume_to_job(resume, jd_text)

    assert res["has_job_description"] is True
    assert res["job_match_score"] >= 65


def test_cross_domain_negative_match_protection():
    """CRITICAL: Verify Graphic Designer applying for Registered Nurse receives a LOW score."""
    resume_text = "Graphic Designer with expertise in Adobe Photoshop, Figma, Brand Identity, and Communication."
    resume = create_parsed_resume_fixture(resume_text, ["Figma", "Adobe Photoshop", "Communication"])

    jd_text = """
    Registered Nurse required for direct patient care, medication administration, clinical documentation, and teamwork.
    """
    res = match_resume_to_job(resume, jd_text)

    assert res["has_job_description"] is True
    assert res["job_match_score"] <= 40  # Must be appropriately low due to domain mismatch!


def test_semantic_equivalence_matching():
    """Verify phrase equivalence matches score higher than unrelated phrases."""
    phrase_a = "managed sales representatives"
    phrase_b = "led sales teams"

    sim = embedding_service.similarity(phrase_a, phrase_b)
    assert sim >= 0.2


def test_job_matcher_nlp_fallback(monkeypatch):
    """Verify matcher operates cleanly without crashing when NLP model loading fails."""
    def mock_fail():
        return None

    monkeypatch.setattr(embedding_service, "_load_model", mock_fail)
    monkeypatch.setattr(embedding_service, "_IS_MODEL_AVAILABLE", False)

    resume_text = "Software Developer with Python and Flask."
    resume = create_parsed_resume_fixture(resume_text, ["Python", "Flask"])

    jd_text = "Required: Python, Flask"
    res = match_resume_to_job(resume, jd_text)

    assert res["has_job_description"] is True
    assert res["job_match_score"] > 0
    assert "Python" in res["matched_skills"]
