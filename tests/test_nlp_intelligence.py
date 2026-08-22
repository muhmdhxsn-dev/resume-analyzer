import pytest
from services.nlp import embedding_service
from services.nlp.domain_detector import detect_domains_and_roles
from services.nlp.semantic_skill_extractor import extract_categorized_skills
from services.candidate_profile import build_candidate_profile
from services.resume_parser import parse_resume


def test_semantic_similarity_phrases():
    """Verify semantic similarity for related vs unrelated phrases."""
    rel_sim = embedding_service.similarity("managed sales team", "led sales representatives")
    assert rel_sim >= 0.2

    unrel_sim = embedding_service.similarity("managed sales team", "patient phlebotomy triage")
    assert unrel_sim <= rel_sim


def test_domain_detection_multidomain():
    """Verify domain detection across Tech, Finance, Marketing, Healthcare, and Education."""
    # 1. Tech
    tech_text = "Software Engineer with experience in Python, Flask, Docker, and REST APIs."
    domains, roles = detect_domains_and_roles(tech_text)
    assert len(domains) > 0
    assert domains[0]["domain"] == "Software Engineering & IT"
    assert domains[0]["confidence"] >= 0.15

    # 2. Finance
    finance_text = "Senior Accountant specializing in Financial Reporting, Auditing, General Ledger, and Accounts Payable."
    domains, roles = detect_domains_and_roles(finance_text)
    assert len(domains) > 0
    assert domains[0]["domain"] == "Finance & Accounting"

    # 3. Healthcare
    healthcare_text = "Registered Nurse experienced in Patient Care, Clinical Documentation, Vital Signs, and EHR."
    domains, roles = detect_domains_and_roles(healthcare_text)
    assert len(domains) > 0
    assert domains[0]["domain"] == "Healthcare & Medicine"

    # 4. Education
    education_text = "Educator specializing in Lesson Planning, Classroom Management, and Curriculum Development."
    domains, roles = detect_domains_and_roles(education_text)
    assert len(domains) > 0
    assert domains[0]["domain"] == "Education & Teaching"


def test_categorized_skills_extraction():
    """Verify skill categorization into technical_skills, tools, soft_skills, and domain_competencies."""
    text = "Experienced Finance Manager skilled in Financial Reporting, Excel, QuickBooks, Leadership, and Accounts Payable."
    cats = extract_categorized_skills(text)

    assert "Excel" in cats["tools"] or "QuickBooks" in cats["tools"]
    assert "Leadership" in cats["soft_skills"]
    assert "Financial Reporting" in cats["technical_skills"] or "Financial Reporting" in cats["domain_competencies"]


def test_candidate_profile_builder():
    """Verify normalized CandidateProfile generation."""
    parsed_mock = {
        "cleaned_text": "Marketing Manager with 5 years experience in Digital Marketing, SEO, Google Analytics, and Campaign Management.",
        "sections": {
            "summary": "Marketing Manager with 5 years experience in Digital Marketing.",
            "skills": "SEO, Digital Marketing, Google Analytics"
        },
        "skills": ["SEO", "Digital Marketing", "Google Analytics"]
    }
    profile = build_candidate_profile(parsed_mock)

    assert len(profile["domains"]) > 0
    assert profile["domains"][0]["domain"] == "Marketing & Sales"
    assert profile["years_of_experience"] == 5.0
    assert "categorized_skills" in profile
    assert "technical_skills" in profile["categorized_skills"]


def test_nlp_fallback_handling(monkeypatch):
    """Verify system falls back cleanly when model loading is forced to fail."""
    def mock_fail():
        return None

    monkeypatch.setattr(embedding_service, "_load_model", mock_fail)
    monkeypatch.setattr(embedding_service, "_IS_MODEL_AVAILABLE", False)

    # Similarity should fall back to token overlap without throwing
    sim = embedding_service.similarity("python developer", "software python developer")
    assert sim > 0.0

    # Domain detection should function using keyword fallback
    domains, _ = detect_domains_and_roles("Software Engineer Python Flask")
    assert len(domains) > 0
