import pytest
from services.resume_analyzer import analyze_resume, extract_features, calculate_scores, CATEGORY_WEIGHTS


def create_sample_resume_dict(
    cleaned_text: str = "",
    sections: dict = None,
    skills: list = None,
    page_count: int = 1
) -> dict:
    """Helper fixture generator to construct parsed resume dicts for testing."""
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


def test_empty_resume_analysis():
    """Verify empty resume score is 0 and produces valid error warnings."""
    parsed = create_sample_resume_dict("")
    res = analyze_resume(parsed)

    assert res["score"] == 0
    assert res["max_score"] == 100
    assert res["categories"]["contact_information"]["score"] == 0
    assert res["categories"]["experience"]["score"] == 0
    assert len(res["warnings"]) > 0


def test_complete_high_quality_resume_analysis():
    """Verify complete high-quality resume achieves a score close to 100."""
    cleaned = """John Doe
Email: john.doe@example.com | Phone: +1-555-0199 | LinkedIn: linkedin.com/in/johndoe | GitHub: github.com/johndoe

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

    parsed = create_sample_resume_dict(cleaned, sections, skills, page_count=2)
    res = analyze_resume(parsed)

    assert res["score"] >= 90
    assert res["score"] <= 100
    assert len(res["strengths"]) >= 4
    assert res["categories"]["contact_information"]["score"] == 10
    assert res["categories"]["skills"]["score"] == 20


def test_contact_information_detection():
    """Verify contact info feature detection (Email, Phone, LinkedIn, GitHub)."""
    text = "Jane Smith | jane@test.org | +92 300 1234567 | linkedin.com/in/janesmith | github.com/janesmith"
    features = extract_features(create_sample_resume_dict(text))

    assert features["has_email"] is True
    assert features["has_phone"] is True
    assert features["has_linkedin"] is True
    assert features["has_github"] is True


def test_summary_scoring_variations():
    """Verify summary section scoring rules."""
    # Strong summary (>= 20 words, contains role title, contains skill)
    strong_summary = "Experienced Software Engineer with a passion for developing scalable web apps using Python and Flask. Skilled in leading cross-functional developer teams."
    parsed_strong = create_sample_resume_dict(strong_summary, {"summary": strong_summary})
    res_strong = analyze_resume(parsed_strong)
    assert res_strong["categories"]["summary"]["score"] == 10

    # Short basic summary
    short_summary = "Hello world summary."
    parsed_short = create_sample_resume_dict(short_summary, {"summary": short_summary})
    res_short = analyze_resume(parsed_short)
    assert res_short["categories"]["summary"]["score"] == 4  # Exists only


def test_skills_tier_scoring():
    """Verify skills section scoring based on skill count tiers."""
    # Tier 0: 0 skills -> 0 points
    res_0 = analyze_resume(create_sample_resume_dict("", skills=[]))
    assert res_0["categories"]["skills"]["score"] == 0

    # Tier 1: 2 skills -> 5 points
    res_1 = analyze_resume(create_sample_resume_dict("", skills=["Python", "Flask"]))
    assert res_1["categories"]["skills"]["score"] == 5

    # Tier 2: 4 skills -> 10 points
    res_2 = analyze_resume(create_sample_resume_dict("", skills=["Python", "Flask", "Docker", "Git"]))
    assert res_2["categories"]["skills"]["score"] == 10

    # Tier 3: 6 skills -> 15 points
    res_3 = analyze_resume(create_sample_resume_dict("", skills=["Python", "Flask", "Docker", "Git", "React", "SQL"]))
    assert res_3["categories"]["skills"]["score"] == 15

    # Tier 4: 9 skills -> 20 points
    res_4 = analyze_resume(create_sample_resume_dict("", skills=["Python", "Flask", "Docker", "Git", "React", "SQL", "AWS", "Redis", "Linux"]))
    assert res_4["categories"]["skills"]["score"] == 20


def test_experience_scoring_action_verbs_and_metrics():
    """Verify experience scoring for action verbs and metrics."""
    exp_text = """Developer at Company A (2020 - Present)
    - Implemented microservices architecture handling over 100,000 daily active users with sub-millisecond response latency.
    - Optimized SQL database queries and redis cache layers, reducing server response times by 40 percent.
    - Built automated CI/CD deployment pipelines using GitHub Actions and managed AWS cloud infrastructure deployments.
    """
    parsed = create_sample_resume_dict(exp_text, {"experience": exp_text})
    res = analyze_resume(parsed)

    assert res["categories"]["experience"]["score"] == 25
    assert any("action verbs" in s for s in res["strengths"])


def test_projects_scoring():
    """Verify projects section scoring."""
    proj_text = """Personal Web Application Portfolio
    - Built responsive modern web UI using React, Tailwind CSS, and Python Flask REST API backend services.
    - Deployed cloud application infrastructure on AWS EC2 with automated Docker builds, serving over 1,000 monthly active users cleanly.
    """
    parsed = create_sample_resume_dict(proj_text, {"projects": proj_text})
    res = analyze_resume(parsed)

    assert res["categories"]["projects"]["score"] == 15


def test_education_degree_and_institution():
    """Verify education section degree and institution matching."""
    edu_text = "Bachelor of Science in Computer Science | State University"
    parsed = create_sample_resume_dict(edu_text, {"education": edu_text})
    res = analyze_resume(parsed)

    assert res["categories"]["education"]["score"] == 10


def test_certifications_scoring():
    """Verify certifications section scoring."""
    cert_text = "AWS Certified Developer - Associate"
    parsed = create_sample_resume_dict(cert_text, {"certifications": cert_text})
    res = analyze_resume(parsed)

    assert res["categories"]["certifications"]["score"] == 5


def test_resume_length_scoring():
    """Verify page count / word count length scoring."""
    # 1-2 pages -> 5 points
    res_2p = analyze_resume(create_sample_resume_dict("Text sample", page_count=2))
    assert res_2p["categories"]["length"]["score"] == 5

    # 3 pages -> 3 points
    res_3p = analyze_resume(create_sample_resume_dict("Text sample", page_count=3))
    assert res_3p["categories"]["length"]["score"] == 3

    # 5 pages -> 1 point
    res_5p = analyze_resume(create_sample_resume_dict("Text sample", page_count=5))
    assert res_5p["categories"]["length"]["score"] == 1


def test_score_safety_bounds_and_sum():
    """Verify score bounds (0 <= score <= 100) and total equals category sum."""
    text = "Python, Flask, Engineer, Developed, University, Bachelor"
    sections = {"skills": "Python, Flask", "summary": "Software Engineer"}
    parsed = create_sample_resume_dict(text, sections=sections, skills=["Python", "Flask"])
    res = analyze_resume(parsed)

    # 1. Bounds check
    assert 0 <= res["score"] <= 100

    # 2. Category max bounds check
    for cat_name, cat_data in res["categories"].items():
        assert 0 <= cat_data["score"] <= cat_data["max_score"]

    # 3. Sum equality check
    cat_sum = sum(c["score"] for c in res["categories"].values())
    assert res["score"] == int(round(cat_sum))


def test_feedback_generation_warnings_and_recommendations():
    """Verify warnings and recommendations generated when sections/links are missing."""
    text = "John Doe\nEmail: john@example.com\n\nSKILLS\nPython"
    parsed = create_sample_resume_dict(text, sections={"skills": "Python"}, skills=["Python"])
    res = analyze_resume(parsed)

    assert "No LinkedIn profile link detected." in res["warnings"]
    assert any("LinkedIn" in r for r in res["recommendations"])
    assert "No work experience section detected." in res["warnings"]
    assert "No dedicated projects section detected." in res["warnings"]
