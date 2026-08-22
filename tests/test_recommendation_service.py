import pytest
from services.resume_analyzer import analyze_resume
from services.job_matcher import match_resume_to_job
from services.recommendation_service import generate_recommendations, generate_general_recommendations, generate_job_recommendations


def create_sample_parsed_resume(cleaned_text: str = "", sections: dict = None, skills: list = None, page_count: int = 1) -> dict:
    """Helper fixture generator to construct mock parsed resume dicts."""
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
        "filename": "test_resume.pdf",
        "file_type": "pdf",
        "page_count": page_count if cleaned_text.strip() else None,
        "raw_text": cleaned_text,
        "cleaned_text": cleaned_text,
        "has_text": bool(cleaned_text.strip()),
        "sections": default_sections,
        "skills": skills or [],
        "error": None
    }


def test_weak_resume_recommendation_generation():
    """Verify weak resume generates HIGH and MEDIUM priority recommendations."""
    weak_text = "John Doe\n\nSKILLS\nPython"
    parsed = create_sample_parsed_resume(weak_text, sections={"skills": "Python"}, skills=["Python"])
    analysis = analyze_resume(parsed)
    plan = generate_recommendations(analysis)

    assert plan["counts"]["total"] > 0
    assert plan["counts"]["high"] > 0
    
    # Priority sorting check
    priorities = [r["priority"] for r in plan["all_recommendations"]]
    p_values = [{"HIGH": 0, "MEDIUM": 1, "LOW": 2}[p] for p in priorities]
    assert p_values == sorted(p_values)


def test_strong_resume_no_false_negative_recommendations():
    """Verify strong complete resume generates minimal negative recommendations."""
    strong_text = """John Doe
    Email: john@example.com | Phone: +1-555-0199 | LinkedIn: linkedin.com/in/johndoe | GitHub: github.com/johndoe
    
    SUMMARY
    Experienced Senior Software Engineer with 8+ years building scalable Python web applications and microservices. Dedicated to building robust tools and leading agile software engineering teams.
    
    SKILLS
    Python, Flask, Django, PostgreSQL, Docker, Kubernetes, AWS, React, Git
    
    EXPERIENCE
    Senior Software Engineer at Tech Corp (2020 - Present)
    - Developed and deployed high-performance microservices handling 5,000 requests/sec.
    - Optimized database queries, reducing response latency by 35%.
    - Built automated CI/CD pipelines using GitHub Actions to streamline software releases across globally distributed teams and cloud infrastructure.
    
    PROJECTS
    Resume Analyzer App
    - Architected REST API backend using Python and Flask.
    - Implemented automated test suite with 95% code coverage to validate document parsing, section detection, skill extraction, and quality scoring engines.
    
    EDUCATION
    B.S. Computer Science | State University (2016)
    
    CERTIFICATIONS
    AWS Certified Solutions Architect
    """
    sections = {
        "summary": "Experienced Senior Software Engineer with 8+ years building scalable Python web applications and microservices. Dedicated to building robust tools and leading agile software engineering teams.",
        "skills": "Python, Flask, Django, PostgreSQL, Docker, Kubernetes, AWS, React, Git",
        "experience": "Senior Software Engineer at Tech Corp (2020 - Present)\n- Developed and deployed high-performance microservices handling 5,000 requests/sec.\n- Optimized database queries, reducing response latency by 35%.\n- Built automated CI/CD pipelines using GitHub Actions to streamline software releases across globally distributed teams and cloud infrastructure.",
        "projects": "Resume Analyzer App\n- Architected REST API backend using Python and Flask.\n- Implemented automated test suite with 95% code coverage to validate document parsing, section detection, skill extraction, and quality scoring engines.",
        "education": "B.S. Computer Science | State University (2016)",
        "certifications": "AWS Certified Solutions Architect"
    }
    skills = ["Python", "Flask", "Django", "PostgreSQL", "Docker", "Kubernetes", "AWS", "React", "Git"]

    parsed = create_sample_parsed_resume(strong_text, sections, skills, page_count=2)
    analysis = analyze_resume(parsed)
    plan = generate_recommendations(analysis)

    assert plan["counts"]["high"] == 0


def test_missing_contact_info_recommendations():
    """Verify missing email/phone generate HIGH priority and missing LinkedIn/GitHub generate LOW priority."""
    text = "John Doe\n\nSUMMARY\nSoftware Developer with experience."
    parsed = create_sample_parsed_resume(text, sections={"summary": "Software Developer with experience."})
    analysis = analyze_resume(parsed)
    recs = generate_general_recommendations(analysis)

    rec_ids = {r["id"]: r for r in recs}
    assert "rec_contact_email" in rec_ids
    assert rec_ids["rec_contact_email"]["priority"] == "HIGH"
    assert "rec_contact_phone" in rec_ids
    assert rec_ids["rec_contact_phone"]["priority"] == "HIGH"
    assert "rec_contact_linkedin" in rec_ids
    assert rec_ids["rec_contact_linkedin"]["priority"] == "LOW"


def test_missing_summary_recommendation():
    """Verify missing summary section generates HIGH priority summary recommendation."""
    text = "John Doe | john@example.com | 555-1234\n\nSKILLS\nPython"
    parsed = create_sample_parsed_resume(text, sections={"skills": "Python"})
    analysis = analyze_resume(parsed)
    recs = generate_general_recommendations(analysis)

    rec_ids = {r["id"]: r for r in recs}
    assert "rec_summary_missing" in rec_ids
    assert rec_ids["rec_summary_missing"]["priority"] == "HIGH"


def test_missing_experience_and_metrics_recommendations():
    """Verify experience metrics recommendation is emitted when experience lacks numbers."""
    exp_text = "Software Developer at Company A\n- Worked on python web applications and maintained servers."
    parsed = create_sample_parsed_resume(exp_text, sections={"experience": exp_text})
    analysis = analyze_resume(parsed)
    recs = generate_general_recommendations(analysis)

    rec_ids = {r["id"]: r for r in recs}
    assert "rec_experience_metrics" in rec_ids
    assert rec_ids["rec_experience_metrics"]["priority"] == "HIGH"


def test_missing_required_job_skills_recommendation_and_non_fabrication():
    """Verify missing required job skills generate HIGH priority recommendation without telling user to fabricate."""
    jd_text = """
    Required:
    Django, Redis, AWS
    """
    parsed = create_sample_parsed_resume("Python, Flask", sections={"skills": "Python, Flask"}, skills=["Python", "Flask"])
    job_match = match_resume_to_job(parsed, jd_text)
    recs = generate_job_recommendations(job_match)

    assert len(recs) > 0
    req_rec = recs[0]
    assert req_rec["id"] == "rec_job_missing_required"
    assert req_rec["priority"] == "HIGH"
    assert "Django" in req_rec["action"]
    
    # Non-fabrication check: ensure action tells user to add IF they have genuine experience
    assert "If you have genuine experience" in req_rec["action"]
    assert "consider gaining practical experience before claiming" in req_rec["action"]


def test_missing_preferred_job_skills_recommendation():
    """Verify missing preferred job skills generate MEDIUM priority recommendation."""
    jd_text = """
    Required:
    Python
    
    Preferred:
    Kubernetes
    """
    parsed = create_sample_parsed_resume("Python", sections={"skills": "Python"}, skills=["Python"])
    job_match = match_resume_to_job(parsed, jd_text)
    recs = generate_job_recommendations(job_match)

    pref_rec = [r for r in recs if r["id"] == "rec_job_missing_preferred"][0]
    assert pref_rec["priority"] == "MEDIUM"
    assert "Kubernetes" in pref_rec["action"]


def test_no_job_description_no_job_recommendations():
    """Verify omitting job description produces empty job_improvements."""
    parsed = create_sample_parsed_resume("Python Developer", sections={"summary": "Python Developer"})
    analysis = analyze_resume(parsed)
    plan = generate_recommendations(analysis, job_match=None)

    assert plan["has_job_recommendations"] is False
    assert len(plan["job_improvements"]) == 0
    assert len(plan["resume_improvements"]) > 0


def test_recommendation_3part_structure():
    """Verify every recommendation strictly contains problem, why_it_matters, and action."""
    parsed = create_sample_parsed_resume("Sample text")
    analysis = analyze_resume(parsed)
    plan = generate_recommendations(analysis)

    for rec in plan["all_recommendations"]:
        assert "id" in rec
        assert "category" in rec
        assert "priority" in rec
        assert "title" in rec
        assert len(rec["problem"].strip()) > 0
        assert len(rec["why_it_matters"].strip()) > 0
        assert len(rec["action"].strip()) > 0
