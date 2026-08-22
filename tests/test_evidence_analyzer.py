import pytest
from services.evidence_analyzer import (
    normalize_skill,
    analyze_skill_locations,
    evaluate_evidence_strength,
    analyze_resume_evidence
)
from services.job_matcher import match_resume_to_job
from services.resume_analyzer import analyze_resume
from services.recommendation_service import generate_recommendations


def create_parsed_resume_mock(sections: dict = None, skills: list = None, cleaned_text: str = "") -> dict:
    """Helper fixture generator for evidence analyzer tests."""
    default_sections = {
        "summary": "",
        "skills": "",
        "experience": "",
        "education": "",
        "projects": "",
        "certifications": ""
    }
    if sections:
        default_sections.update(sections)

    return {
        "filename": "evidence_test.pdf",
        "file_type": "pdf",
        "page_count": 1,
        "raw_text": cleaned_text,
        "cleaned_text": cleaned_text or "\n".join(default_sections.values()),
        "has_text": True,
        "sections": default_sections,
        "skills": skills or [],
        "error": None
    }


def test_normalize_skill_aliases_and_case():
    """Verify alias normalization and case insensitivity."""
    assert normalize_skill("postgres") == "PostgreSQL"
    assert normalize_skill("postgresql") == "PostgreSQL"
    assert normalize_skill("psql") == "PostgreSQL"
    assert normalize_skill("rest api") == "REST API"
    assert normalize_skill("restful apis") == "REST API"
    assert normalize_skill("k8s") == "Kubernetes"
    assert normalize_skill("amazon web services") == "AWS"
    assert normalize_skill("python") == "Python"
    assert normalize_skill("PYTHON") == "Python"


def test_evidence_strength_rules():
    """Verify evidence strength classification rules."""
    # 1. Skills ONLY -> WEAK
    assert evaluate_evidence_strength(in_skills=True, in_exp=False, in_proj=False) == "WEAK"

    # 2. Skills + Experience -> STRONG
    assert evaluate_evidence_strength(in_skills=True, in_exp=True, in_proj=False) == "STRONG"

    # 3. Skills + Projects -> MODERATE
    assert evaluate_evidence_strength(in_skills=True, in_exp=False, in_proj=True) == "MODERATE"

    # 4. Experience + Projects -> STRONG
    assert evaluate_evidence_strength(in_skills=False, in_exp=True, in_proj=True) == "STRONG"

    # 5. Experience ONLY -> MODERATE
    assert evaluate_evidence_strength(in_skills=False, in_exp=True, in_proj=False) == "MODERATE"

    # 6. Missing everywhere -> MISSING
    assert evaluate_evidence_strength(in_skills=False, in_exp=False, in_proj=False) == "MISSING"


def test_skill_location_analysis():
    """Verify skill section detection across Skills, Experience, and Projects."""
    sections = {
        "skills": "Python, Docker, PostgreSQL",
        "experience": "Software Engineer at Tech Corp\n- Built web applications using Python and PostgreSQL.",
        "projects": "Personal App\n- Containerized microservices using Docker."
    }
    
    python_locs = analyze_skill_locations("Python", sections)
    assert python_locs["in_skills_section"] is True
    assert python_locs["in_experience"] is True
    assert python_locs["in_projects"] is False

    docker_locs = analyze_skill_locations("Docker", sections)
    assert docker_locs["in_skills_section"] is True
    assert docker_locs["in_experience"] is False
    assert docker_locs["in_projects"] is True

    aws_locs = analyze_skill_locations("AWS", sections)
    assert aws_locs["in_skills_section"] is False
    assert aws_locs["in_experience"] is False
    assert aws_locs["in_projects"] is False


def test_general_evidence_analysis_without_job_description():
    """Verify general skill evidence analysis works cleanly without a job description."""
    sections = {
        "skills": "Python, Docker, AWS",
        "experience": "Senior Developer\n- Developed scalable backends in Python.",
        "projects": "DevOps Pipeline\n- Configured Docker containers."
    }
    parsed = create_parsed_resume_mock(sections, skills=["Python", "Docker", "AWS"])
    res = analyze_resume_evidence(parsed, job_match=None)

    assert res["has_job_description"] is False
    assert res["evidence_strength_score"] > 0
    assert len(res["skill_evidence_list"]) >= 3

    evidence_map = {item["skill"]: item["evidence_strength"] for item in res["skill_evidence_list"]}
    assert evidence_map.get("Python") == "STRONG"
    assert evidence_map.get("Docker") == "MODERATE"
    assert evidence_map.get("AWS") == "WEAK"


def test_job_evidence_matrix_and_gaps():
    """Verify job evidence matrix and evidence gaps identification."""
    sections = {
        "skills": "Python, Flask, Docker, PostgreSQL",
        "experience": "Senior Python Developer\n- Developed REST APIs in Python and Flask.",
        "projects": "Analytics App\n- Built dashboard using PostgreSQL."
    }
    parsed = create_parsed_resume_mock(sections, skills=["Python", "Flask", "Docker", "PostgreSQL"])
    
    jd_text = """
    Required:
    Python, Flask, Docker, Redis
    
    Preferred:
    PostgreSQL, AWS
    """
    job_match = match_resume_to_job(parsed, jd_text)
    res = analyze_resume_evidence(parsed, job_match)

    assert res["has_job_description"] is True
    matrix = res["job_evidence_matrix"]
    assert len(matrix) >= 6

    matrix_map = {item["skill"]: item for item in matrix}

    # Python: Skills + Experience -> STRONG
    assert matrix_map["Python"]["matched"] is True
    assert matrix_map["Python"]["evidence_strength"] == "STRONG"

    # Docker: Skills ONLY -> WEAK -> Evidence Gap
    assert matrix_map["Docker"]["matched"] is True
    assert matrix_map["Docker"]["evidence_strength"] == "WEAK"

    # Redis: Missing -> MISSING
    assert matrix_map["Redis"]["matched"] is False
    assert matrix_map["Redis"]["evidence_strength"] == "MISSING"

    # Gaps check
    gap_skills = [g["skill"] for g in res["evidence_gaps"]]
    assert "Docker" in gap_skills
    assert "Python" not in gap_skills  # Strong evidence -> no gap
    assert "Redis" not in gap_skills   # Missing skill -> Phase 6 missing skill, not evidence gap


def test_integration_with_phase_7_recommendations():
    """Verify Phase 7 recommendation engine consumes Phase 8 evidence gaps."""
    sections = {
        "skills": "Python, Docker",
        "experience": "Developer\n- Built apps in Python."
    }
    parsed = create_parsed_resume_mock(sections, skills=["Python", "Docker"])
    jd_text = "Required: Python, Docker"
    
    job_match = match_resume_to_job(parsed, jd_text)
    evidence_res = analyze_resume_evidence(parsed, job_match)
    analysis = analyze_resume(parsed)

    plan = generate_recommendations(analysis, job_match, evidence_res)

    gap_recs = [r for r in plan["job_improvements"] if "Docker" in r["title"] or "Docker" in r["problem"]]
    assert len(gap_recs) > 0
    rec = gap_recs[0]
    assert rec["priority"] == "HIGH"
    assert "Strengthen Docker" in rec["title"]
    assert "If you have genuine Docker experience" in rec["action"]


def test_duplicate_skills_and_case_normalization_in_matrix():
    """Verify duplicates and case variations yield one canonical skill entry in evidence matrix."""
    sections = {
        "skills": "python, PYTHON, Python, postgres, PostgreSQL"
    }
    parsed = create_parsed_resume_mock(sections, skills=["Python", "PostgreSQL"])
    jd_text = "Required: python, postgresql"
    
    job_match = match_resume_to_job(parsed, jd_text)
    res = analyze_resume_evidence(parsed, job_match)

    skills_in_matrix = [item["skill"] for item in res["job_evidence_matrix"]]
    assert skills_in_matrix.count("Python") == 1
    assert skills_in_matrix.count("PostgreSQL") == 1
