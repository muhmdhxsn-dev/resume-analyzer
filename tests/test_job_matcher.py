import pytest
from services.job_matcher import analyze_job_description, match_resume_to_job


def create_sample_resume_object(skills: list[str]) -> dict:
    """Helper fixture to create a mock parsed resume dictionary."""
    return {
        "filename": "sample_resume.pdf",
        "file_type": "pdf",
        "page_count": 1,
        "raw_text": "Sample text",
        "cleaned_text": "Sample text",
        "has_text": True,
        "sections": {
            "summary": "Sample summary",
            "skills": ", ".join(skills),
            "experience": "Sample experience",
            "education": "Sample education",
            "projects": "Sample projects",
            "certifications": ""
        },
        "skills": skills,
        "error": None
    }


def test_analyze_job_description_required_vs_preferred():
    """Verify job description skill classification into required vs preferred."""
    jd_text = """
    We are seeking a Software Engineer.
    
    Required Qualifications:
    - Must have 3+ years experience with Python and Flask.
    - Strong knowledge of PostgreSQL database.
    - Required skill: Docker.
    
    Preferred / Nice to Have:
    - Experience with Kubernetes is a plus.
    - Familiarity with AWS cloud services.
    """
    
    analysis = analyze_job_description(jd_text)
    
    assert "Python" in analysis["required"]
    assert "Flask" in analysis["required"]
    assert "PostgreSQL" in analysis["required"]
    assert "Docker" in analysis["required"]
    
    assert "Kubernetes" in analysis["preferred"]
    assert "AWS" in analysis["preferred"]
    assert len(analysis["all_jd_skills"]) >= 6


def test_perfect_job_match():
    """Verify 100% job match score when candidate possesses all required and preferred skills."""
    jd_text = """
    Required: Python, Flask, Docker
    Preferred: AWS, PostgreSQL
    """
    resume = create_sample_resume_object(["Python", "Flask", "Docker", "AWS", "PostgreSQL"])
    res = match_resume_to_job(resume, jd_text)
    
    assert res["has_job_description"] is True
    assert res["job_match_score"] == 100
    assert len(res["matched_skills"]) == 5
    assert len(res["missing_required_skills"]) == 0
    assert len(res["missing_preferred_skills"]) == 0


def test_partial_job_match():
    """Verify weighted score calculation for partial match (80% required, 20% preferred)."""
    jd_text = """
    Required: Python, Flask, Docker, PostgreSQL
    Preferred: AWS, Kubernetes
    """
    # Candidate has 2 of 4 required (50% * 80 = 40 pts) + 1 of 2 preferred (50% * 20 = 10 pts) -> 50 pts
    resume = create_sample_resume_object(["Python", "Flask", "AWS"])
    res = match_resume_to_job(resume, jd_text)

    assert res["has_job_description"] is True
    assert res["job_match_score"] == 50
    assert "Docker" in res["missing_required_skills"]
    assert "PostgreSQL" in res["missing_required_skills"]
    assert "Kubernetes" in res["missing_preferred_skills"]


def test_zero_job_match_no_overlapping_skills():
    """Verify 0% job match score when candidate has skills but none match the job requirements."""
    jd_text = """
    Required: Java, Spring Boot, Oracle
    """
    resume = create_sample_resume_object(["Python", "Flask", "Docker"])
    res = match_resume_to_job(resume, jd_text)

    assert res["has_job_description"] is True
    assert res["job_match_score"] == 0
    assert "Java" in res["missing_required_skills"]
    assert "Spring Boot" in res["missing_required_skills"]


def test_job_description_no_recognized_skills():
    """Verify handling when JD contains no skills recognized in catalog."""
    jd_text = "Looking for a punctual person with a positive attitude."
    resume = create_sample_resume_object(["Python", "Flask"])
    res = match_resume_to_job(resume, jd_text)

    assert res["has_job_description"] is True
    assert res["job_match_score"] == 0
    assert any("No recognized skills" in r for r in res["recommendations"])


def test_jd_duplicate_skills_and_case_variations():
    """Verify deduplication and case normalization in JD skill extraction."""
    jd_text = "Required: python, PYTHON, Python, postgres, PostgreSQL"
    analysis = analyze_job_description(jd_text)

    assert len(analysis["all_jd_skills"]) == 2
    assert "Python" in analysis["all_jd_skills"]
    assert "PostgreSQL" in analysis["all_jd_skills"]


def test_empty_or_whitespace_job_description():
    """Verify handling of empty or whitespace job description input."""
    resume = create_sample_resume_object(["Python", "Flask"])

    res1 = match_resume_to_job(resume, "")
    assert res1["has_job_description"] is False
    assert res1["job_match_score"] == 0

    res2 = match_resume_to_job(resume, "   \n\t  ")
    assert res2["has_job_description"] is False
    assert res2["job_match_score"] == 0
