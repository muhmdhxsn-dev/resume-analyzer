import pytest
from services.resume_analyzer import analyze_resume, select_scoring_profile, DOMAIN_PROFILES
from services.candidate_profile import build_candidate_profile


def create_parsed_resume_fixture(cleaned_text: str, sections: dict = None, skills: list = None) -> dict:
    """Helper fixture generator for adaptive scoring tests."""
    sec = {
        "summary": "",
        "skills": "",
        "experience": "",
        "education": "",
        "projects": "",
        "certifications": ""
    }
    if sections:
        sec.update(sections)

    parsed = {
        "filename": "test_adaptive.pdf",
        "file_type": "pdf",
        "page_count": 1,
        "raw_text": cleaned_text,
        "cleaned_text": cleaned_text,
        "has_text": True,
        "sections": sec,
        "skills": skills or [],
        "error": None
    }
    # Attach CandidateProfile
    parsed["candidate_profile"] = build_candidate_profile(parsed)
    return parsed


def test_software_engineer_adaptive_scoring():
    """Verify Software Engineer profile emphasizes projects, skills, and tech context."""
    text = """
    Jane Doe - Senior Full-Stack Engineer
    Email: jane@example.com | Phone: 555-0199 | LinkedIn: linkedin.com/in/janedoe | GitHub: github.com/janedoe
    
    Summary:
    Experienced Software Engineer with 7 years specializing in Python, React, PostgreSQL, and AWS.
    
    Skills:
    Python, React, PostgreSQL, AWS, Docker, Kubernetes, REST API, GraphQL
    
    Experience:
    Senior Developer at Tech Corp (2020 - Present)
    - Architected microservices architecture handling 5M+ daily API requests using Python and FastAPI.
    - Improved database query performance by 40% using PostgreSQL indexing.
    
    Projects:
    E-Commerce Microservices Platform
    - Built reactive dashboard using React and GraphQL.
    
    Education:
    Bachelor of Science in Computer Science - State University
    """
    resume = create_parsed_resume_fixture(text, {
        "summary": "Experienced Software Engineer with 7 years specializing in Python, React, PostgreSQL, and AWS.",
        "skills": "Python, React, PostgreSQL, AWS, Docker, Kubernetes, REST API, GraphQL",
        "experience": "Senior Developer at Tech Corp (2020 - Present)\n- Architected microservices architecture handling 5M+ daily API requests using Python and FastAPI.\n- Improved database query performance by 40% using PostgreSQL indexing.",
        "projects": "E-Commerce Microservices Platform\n- Built reactive dashboard using React and GraphQL.",
        "education": "Bachelor of Science in Computer Science - State University"
    }, skills=["Python", "React", "PostgreSQL", "AWS", "Docker", "Kubernetes", "REST API", "GraphQL"])

    res = analyze_resume(resume)
    assert res["score"] >= 85
    assert res["domain"] == "Software Engineering & IT"
    assert res["categories"]["projects"]["max_score"] > 0
    assert len(res["achievements"]) > 0


def test_accountant_adaptive_scoring_no_project_penalty():
    """Verify Accountant profile receives full score potential WITHOUT needing a Projects section."""
    text = """
    Robert Smith - Senior Certified Accountant (CPA)
    Email: robert.smith@accounting.com | Phone: 555-0188 | LinkedIn: linkedin.com/in/robertsmith
    
    Summary:
    Detail-oriented CPA with 8 years of experience in financial reporting, corporate tax compliance, and auditing.
    
    Skills:
    Financial Reporting, Tax Preparation, General Ledger, Auditing, QuickBooks, Excel, Accounts Payable
    
    Experience:
    Senior Accountant at Global Finance LLC (2018 - Present)
    - Managed monthly financial statement preparation and reduced year-end audit adjustments by 25%.
    - Oversaw corporate budget allocations of $12M across 4 regional departments.
    
    Education:
    Bachelor of Science in Accounting - University of Commerce
    
    Certifications:
    Certified Public Accountant (CPA)
    """
    resume = create_parsed_resume_fixture(text, {
        "summary": "Detail-oriented CPA with 8 years of experience in financial reporting, corporate tax compliance, and auditing.",
        "skills": "Financial Reporting, Tax Preparation, General Ledger, Auditing, QuickBooks, Excel, Accounts Payable",
        "experience": "Senior Accountant at Global Finance LLC (2018 - Present)\n- Managed monthly financial statement preparation and reduced year-end audit adjustments by 25%.\n- Oversaw corporate budget allocations of $12M across 4 regional departments.",
        "education": "Bachelor of Science in Accounting - University of Commerce",
        "certifications": "Certified Public Accountant (CPA)"
    }, skills=["Financial Reporting", "Tax Preparation", "General Ledger", "Auditing", "QuickBooks", "Excel", "Accounts Payable"])

    res = analyze_resume(resume)
    # Accountant has NO projects section, but should get top score!
    assert res["score"] >= 85
    assert res["domain"] == "Finance & Accounting"
    assert res["categories"]["projects"]["max_score"] == 0
    assert not any("projects" in w.lower() for w in res["warnings"])


def test_teacher_adaptive_scoring_no_project_penalty():
    """Verify Teacher profile receives high score and zero project penalty."""
    text = """
    Mary Johnson - High School Mathematics Educator
    Email: mary.johnson@school.edu | Phone: 555-0177 | LinkedIn: linkedin.com/in/maryjohnson
    
    Summary:
    Dedicated Mathematics Educator with 6 years of experience in algebra instruction, lesson planning, and curriculum development.
    
    Skills:
    Lesson Planning, Curriculum Development, Classroom Management, Mathematics, Student Assessment, Special Education
    
    Experience:
    Math Teacher at Central High School (2019 - Present)
    - Designed innovative algebra curriculum that increased standardized test pass rates by 18%.
    - Managed classrooms of 30+ students while integrating digital learning technologies.
    
    Education:
    Master of Education in Mathematics Teaching - Teachers College
    
    Certifications:
    State Secondary Teaching Certification in Mathematics
    """
    resume = create_parsed_resume_fixture(text, {
        "summary": "Dedicated Mathematics Educator with 6 years of experience in algebra instruction, lesson planning, and curriculum development.",
        "skills": "Lesson Planning, Curriculum Development, Classroom Management, Mathematics, Student Assessment, Special Education",
        "experience": "Math Teacher at Central High School (2019 - Present)\n- Designed innovative algebra curriculum that increased standardized test pass rates by 18%.\n- Managed classrooms of 30+ students while integrating digital learning technologies.",
        "education": "Master of Education in Mathematics Teaching - Teachers College",
        "certifications": "State Secondary Teaching Certification in Mathematics"
    }, skills=["Lesson Planning", "Curriculum Development", "Classroom Management", "Mathematics", "Student Assessment", "Special Education"])

    res = analyze_resume(resume)
    assert res["score"] >= 80
    assert res["domain"] == "Education & Teaching"
    assert res["categories"]["projects"]["max_score"] == 0


def test_nurse_adaptive_scoring_clinical_focus():
    """Verify Registered Nurse profile emphasizes clinical experience and certifications."""
    text = """
    Sarah Davis - Registered Nurse (RN, BSN)
    Email: sarah.davis@hospital.org | Phone: 555-0166 | LinkedIn: linkedin.com/in/sarahdavisrn
    
    Summary:
    Compassionate Registered Nurse with 5 years of ICU experience specializing in critical patient care and clinical documentation.
    
    Skills:
    Patient Care, Clinical Documentation, Triage, ICU, BLS, ACLS, Patient Assessment, Medication Administration
    
    Experience:
    Intensive Care Nurse at Memorial Hospital (2020 - Present)
    - Provided direct clinical patient care for 150+ high-acuity ICU patients annually with 98% satisfaction rating.
    - Administered critical care medications following strict hospital safety protocols.
    
    Education:
    Bachelor of Science in Nursing (BSN) - State School of Nursing
    
    Certifications:
    Registered Nurse License (RN), Basic Life Support (BLS), Advanced Cardiovascular Life Support (ACLS)
    """
    resume = create_parsed_resume_fixture(text, {
        "summary": "Compassionate Registered Nurse with 5 years of ICU experience specializing in critical patient care and clinical documentation.",
        "skills": "Patient Care, Clinical Documentation, Triage, ICU, BLS, ACLS, Patient Assessment, Medication Administration",
        "experience": "Intensive Care Nurse at Memorial Hospital (2020 - Present)\n- Provided direct clinical patient care for 150+ high-acuity ICU patients annually with 98% satisfaction rating.\n- Administered critical care medications following strict hospital safety protocols.",
        "education": "Bachelor of Science in Nursing (BSN) - State School of Nursing",
        "certifications": "Registered Nurse License (RN), Basic Life Support (BLS), Advanced Cardiovascular Life Support (ACLS)"
    }, skills=["Patient Care", "Clinical Documentation", "Triage", "ICU", "BLS", "ACLS", "Patient Assessment", "Medication Administration"])

    res = analyze_resume(resume)
    assert res["score"] >= 85
    assert res["domain"] == "Healthcare & Medicine"
    assert res["categories"]["projects"]["max_score"] == 0


def test_sales_adaptive_scoring_achievement_boost():
    """Verify Sales Representative profile captures revenue achievements and boosts experience score."""
    text = """
    David Miller - Senior Enterprise Sales Executive
    Email: david.miller@sales.com | Phone: 555-0155 | LinkedIn: linkedin.com/in/davidmillersales
    
    Summary:
    Top-performing Sales Executive with 8 years of enterprise B2B sales, account management, and negotiation experience.
    
    Skills:
    B2B Sales, Account Management, Lead Generation, Sales Strategy, Salesforce, Negotiation, Closing
    
    Experience:
    Enterprise Sales Manager at CloudTech (2019 - Present)
    - Expanded regional client accounts generating $3.4M in new annual recurring revenue.
    - Exceeded annual sales quota by 135% for 3 consecutive years while leading a team of 5 account executives.
    
    Education:
    Bachelor of Business Administration - State Business School
    """
    resume = create_parsed_resume_fixture(text, {
        "summary": "Top-performing Sales Executive with 8 years of enterprise B2B sales, account management, and negotiation experience.",
        "skills": "B2B Sales, Account Management, Lead Generation, Sales Strategy, Salesforce, Negotiation, Closing",
        "experience": "Enterprise Sales Manager at CloudTech (2019 - Present)\n- Expanded regional client accounts generating $3.4M in new annual recurring revenue.\n- Exceeded annual sales quota by 135% for 3 consecutive years while leading a team of 5 account executives.",
        "education": "Bachelor of Business Administration - State Business School"
    }, skills=["B2B Sales", "Account Management", "Lead Generation", "Sales Strategy", "Salesforce", "Negotiation", "Closing"])

    res = analyze_resume(resume)
    assert res["score"] >= 85
    assert res["domain"] == "Marketing & Sales"
    assert len(res["achievements"]) >= 1


def test_achievement_vs_responsibility_scoring_boost():
    """Verify that quantified achievement outcomes provide higher score than plain responsibilities."""
    plain_text = """
    Developer at Tech LLC.
    Responsibilities:
    - Managed software application updates.
    - Handled customer support tickets.
    """
    plain_resume = create_parsed_resume_fixture(plain_text, {
        "experience": "Developer at Tech LLC.\n- Managed software application updates.\n- Handled customer support tickets."
    })

    impact_text = """
    Developer at Tech LLC.
    Achievements:
    - Reduced application crash rate by 35% across 500,000 active users.
    - Accelerated API response speed by 45% saving $12,000 in monthly server costs.
    """
    impact_resume = create_parsed_resume_fixture(impact_text, {
        "experience": "Developer at Tech LLC.\n- Reduced application crash rate by 35% across 500,000 active users.\n- Accelerated API response speed by 45% saving $12,000 in monthly server costs."
    })

    plain_res = analyze_resume(plain_resume)
    impact_res = analyze_resume(impact_resume)

    assert impact_res["categories"]["experience"]["score"] > plain_res["categories"]["experience"]["score"]
    assert len(impact_res["achievements"]) > 0
    assert len(plain_res["achievements"]) == 0


def test_uncertain_domain_fallback_profile():
    """Verify neutral Default profile is selected when candidate domain is uncertain."""
    text = "John Doe. Contact: john@example.com, Phone: 555-0100. General worker with miscellaneous experience."
    resume = create_parsed_resume_fixture(text)
    
    # Force empty domains in candidate_profile
    resume["candidate_profile"] = {"domains": [], "skills": {}}
    res = analyze_resume(resume)

    assert res["domain"] == "Default"
    assert res["categories"]["projects"]["max_score"] == 15
    assert res["score"] >= 0 and res["score"] <= 100
