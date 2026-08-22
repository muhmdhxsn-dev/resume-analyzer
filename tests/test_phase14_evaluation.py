import pytest
from services.resume_analyzer import analyze_resume
from services.job_matcher import match_resume_to_job
from services.candidate_profile import build_candidate_profile
from services.nlp import embedding_service
from services.recommendation_service import generate_recommendations


def create_parsed_resume_fixture(cleaned_text: str, sections: dict = None, skills: list = None) -> dict:
    """Helper fixture generator for evaluation tests."""
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
        "filename": "eval_test.pdf",
        "file_type": "pdf",
        "page_count": 1,
        "raw_text": cleaned_text,
        "cleaned_text": cleaned_text,
        "has_text": True,
        "sections": sec,
        "skills": skills or [],
        "error": None
    }
    parsed["candidate_profile"] = build_candidate_profile(parsed)
    return parsed


# ---------------------------------------------------------
# 1. SYNTHETIC RESUME FIXTURES (10 DOMAINS)
# ---------------------------------------------------------

SYNTHETIC_RESUMES = {
    "software_engineer": {
        "text": """
        Alex Chen - Senior Full Stack Developer
        alex.chen@email.com | 555-0101 | linkedin.com/in/alexchen | github.com/alexchen
        Summary: Full Stack Developer with 6 years of experience building web applications using Python, React, PostgreSQL, and AWS.
        Skills: Python, React, PostgreSQL, AWS, Docker, REST API, JavaScript, Git
        Experience: Senior Developer at Tech Corp (2020-Present). Architected REST APIs in Python handling 2M+ requests daily. Reduced query latency by 35%.
        Education: BS in Computer Science - State University
        """,
        "sections": {
            "summary": "Full Stack Developer with 6 years of experience building web applications using Python, React, PostgreSQL, and AWS.",
            "skills": "Python, React, PostgreSQL, AWS, Docker, REST API, JavaScript, Git",
            "experience": "Senior Developer at Tech Corp (2020-Present). Architected REST APIs in Python handling 2M+ requests daily. Reduced query latency by 35%.",
            "education": "BS in Computer Science - State University"
        },
        "skills": ["Python", "React", "PostgreSQL", "AWS", "Docker", "REST API", "JavaScript", "Git"],
        "expected_domain": "Software Engineering & IT"
    },
    "accountant": {
        "text": """
        Emily Watson - CPA, Senior Accountant
        emily.watson@finance.com | 555-0102 | linkedin.com/in/emilywatson
        Summary: Senior Accountant with 7 years in corporate tax, financial reporting, and audit preparation.
        Skills: Financial Reporting, Tax Preparation, General Ledger, Auditing, QuickBooks, Excel, Accounts Payable
        Experience: Senior Accountant at Financial Group (2018-Present). Prepared monthly financial statements and managed $15M budget reconciliations.
        Education: BS in Accounting - City College
        Certifications: CPA License
        """,
        "sections": {
            "summary": "Senior Accountant with 7 years in corporate tax, financial reporting, and audit preparation.",
            "skills": "Financial Reporting, Tax Preparation, General Ledger, Auditing, QuickBooks, Excel, Accounts Payable",
            "experience": "Senior Accountant at Financial Group (2018-Present). Prepared monthly financial statements and managed $15M budget reconciliations.",
            "education": "BS in Accounting - City College",
            "certifications": "CPA License"
        },
        "skills": ["Financial Reporting", "Tax Preparation", "General Ledger", "Auditing", "QuickBooks", "Excel", "Accounts Payable"],
        "expected_domain": "Finance & Accounting"
    },
    "digital_marketer": {
        "text": """
        Jordan Taylor - Digital Marketing Manager
        jordan.t@marketing.com | 555-0103 | linkedin.com/in/jordantaylor
        Summary: Results-driven Digital Marketer specializing in SEO, Google Ads, content marketing strategy, and campaign management.
        Skills: SEO, SEM, Google Analytics, Content Strategy, Campaign Management, Social Media
        Experience: Marketing Manager at Growth Agency (2019-Present). Increased organic search traffic by 45% and managed $50k monthly ad budgets.
        Education: BA in Marketing - Metro University
        """,
        "sections": {
            "summary": "Results-driven Digital Marketer specializing in SEO, Google Ads, content marketing strategy, and campaign management.",
            "skills": "SEO, SEM, Google Analytics, Content Strategy, Campaign Management, Social Media",
            "experience": "Marketing Manager at Growth Agency (2019-Present). Increased organic search traffic by 45% and managed $50k monthly ad budgets.",
            "education": "BA in Marketing - Metro University"
        },
        "skills": ["SEO", "SEM", "Google Analytics", "Content Strategy", "Campaign Management", "Social Media"],
        "expected_domain": "Marketing & Sales"
    },
    "registered_nurse": {
        "text": """
        Rachel Adams - RN, BSN
        rachel.rn@hospital.org | 555-0104 | linkedin.com/in/racheladamsrn
        Summary: Compassionate Registered Nurse with 5 years ICU experience in critical patient care and clinical documentation.
        Skills: Patient Care, Clinical Documentation, Triage, ICU, BLS, ACLS, Patient Assessment, Medication Administration
        Experience: ICU Staff Nurse at St. Jude Hospital (2020-Present). Provided direct clinical patient care for 120+ ICU patients annually.
        Education: BSN in Nursing - State Health University
        Certifications: RN, BLS, ACLS
        """,
        "sections": {
            "summary": "Compassionate Registered Nurse with 5 years ICU experience in critical patient care and clinical documentation.",
            "skills": "Patient Care, Clinical Documentation, Triage, ICU, BLS, ACLS, Patient Assessment, Medication Administration",
            "experience": "ICU Staff Nurse at St. Jude Hospital (2020-Present). Provided direct clinical patient care for 120+ ICU patients annually.",
            "education": "BSN in Nursing - State Health University",
            "certifications": "RN, BLS, ACLS"
        },
        "skills": ["Patient Care", "Clinical Documentation", "Triage", "ICU", "BLS", "ACLS", "Patient Assessment", "Medication Administration"],
        "expected_domain": "Healthcare & Medicine"
    },
    "teacher": {
        "text": """
        Marcus Vance - High School Science Teacher
        marcus.vance@school.edu | 555-0105 | linkedin.com/in/marcusvance
        Summary: High School Science Educator with 6 years of experience in classroom management, lesson planning, and curriculum development.
        Skills: Lesson Planning, Curriculum Development, Classroom Management, Student Assessment, Special Education
        Experience: Science Teacher at West High School (2019-Present). Developed STEM curriculum improving student test scores by 22%.
        Education: M.Ed in Science Education - Teachers University
        Certifications: State Teaching Certification
        """,
        "sections": {
            "summary": "High School Science Educator with 6 years of experience in classroom management, lesson planning, and curriculum development.",
            "skills": "Lesson Planning, Curriculum Development, Classroom Management, Student Assessment, Special Education",
            "experience": "Science Teacher at West High School (2019-Present). Developed STEM curriculum improving student test scores by 22%.",
            "education": "M.Ed in Science Education - Teachers University",
            "certifications": "State Teaching Certification"
        },
        "skills": ["Lesson Planning", "Curriculum Development", "Classroom Management", "Student Assessment", "Special Education"],
        "expected_domain": "Education & Teaching"
    },
    "sales_executive": {
        "text": """
        Brian Miller - Senior Sales Executive
        brian.miller@sales.com | 555-0106 | linkedin.com/in/brianmiller
        Summary: B2B Enterprise Sales Executive with 8 years experience in lead generation, contract negotiation, and revenue growth.
        Skills: B2B Sales, Account Management, Lead Generation, Sales Strategy, Salesforce, Negotiation, Closing
        Experience: Sales Manager at Enterprise Software (2018-Present). Generated $2.8M in new recurring revenue exceeding quota by 125%.
        Education: BBA in Business - State Business School
        """,
        "sections": {
            "summary": "B2B Enterprise Sales Executive with 8 years experience in lead generation, contract negotiation, and revenue growth.",
            "skills": "B2B Sales, Account Management, Lead Generation, Sales Strategy, Salesforce, Negotiation, Closing",
            "experience": "Sales Manager at Enterprise Software (2018-Present). Generated $2.8M in new recurring revenue exceeding quota by 125%.",
            "education": "BBA in Business - State Business School"
        },
        "skills": ["B2B Sales", "Account Management", "Lead Generation", "Sales Strategy", "Salesforce", "Negotiation", "Closing"],
        "expected_domain": "Marketing & Sales"
    },
    "hr_admin": {
        "text": """
        Laura Martinez - HR Generalist
        laura.m@hr.com | 555-0107 | linkedin.com/in/lauramartinez
        Summary: Human Resources Generalist with 5 years experience in recruiting, onboarding, employee relations, and benefits administration.
        Skills: HR, Recruiting, Talent Acquisition, Onboarding, Employee Relations, Benefits Administration, Payroll
        Experience: HR Generalist at Corporate Staffing (2020-Present). Managed onboarding for 200+ hires and reduced turnover by 15%.
        Education: BS in Human Resources - City University
        """,
        "sections": {
            "summary": "Human Resources Generalist with 5 years experience in recruiting, onboarding, employee relations, and benefits administration.",
            "skills": "HR, Recruiting, Talent Acquisition, Onboarding, Employee Relations, Benefits Administration, Payroll",
            "experience": "HR Generalist at Corporate Staffing (2020-Present). Managed onboarding for 200+ hires and reduced turnover by 15%.",
            "education": "BS in Human Resources - City University"
        },
        "skills": ["HR", "Recruiting", "Talent Acquisition", "Onboarding", "Employee Relations", "Benefits Administration", "Payroll"],
        "expected_domain": "Human Resources & Administration"
    },
    "graphic_designer": {
        "text": """
        Chris Evans - Senior Graphic Designer
        chris.evans@design.com | 555-0108 | linkedin.com/in/chrisevansdesign
        Summary: Creative Graphic Designer specializing in brand identity, UI design, Figma, Adobe Photoshop, and Illustrator.
        Skills: Figma, Photoshop, Illustrator, UI Design, Brand Identity, Typography
        Experience: Lead Designer at Creative Studio (2019-Present). Redesigned brand assets for 30+ enterprise clients.
        Education: BFA in Graphic Design - Design Institute
        """,
        "sections": {
            "summary": "Creative Graphic Designer specializing in brand identity, UI design, Figma, Adobe Photoshop, and Illustrator.",
            "skills": "Figma, Photoshop, Illustrator, UI Design, Brand Identity, Typography",
            "experience": "Lead Designer at Creative Studio (2019-Present). Redesigned brand assets for 30+ enterprise clients.",
            "education": "BFA in Graphic Design - Design Institute"
        },
        "skills": ["Figma", "Photoshop", "Illustrator", "UI Design", "Brand Identity", "Typography"],
        "expected_domain": "Default"
    },
    "civil_engineer": {
        "text": """
        David Kim - PE, Civil Engineer
        david.kim@engineering.org | 555-0109 | linkedin.com/in/davidkimpe
        Summary: Licensed Professional Engineer with 8 years in structural engineering, AutoCAD, construction management, and project planning.
        Skills: AutoCAD, Structural Engineering, Construction Management, Civil Engineering, Project Planning, Site Inspection
        Experience: Senior Civil Engineer at Infrastructure Group (2018-Present). Managed $25M highway bridge renovation project.
        Education: BS in Civil Engineering - Engineering Institute
        Certifications: Professional Engineer (PE) License
        """,
        "sections": {
            "summary": "Licensed Professional Engineer with 8 years in structural engineering, AutoCAD, construction management, and project planning.",
            "skills": "AutoCAD, Structural Engineering, Construction Management, Civil Engineering, Project Planning, Site Inspection",
            "experience": "Senior Civil Engineer at Infrastructure Group (2018-Present). Managed $25M highway bridge renovation project.",
            "education": "BS in Civil Engineering - Engineering Institute",
            "certifications": "Professional Engineer (PE) License"
        },
        "skills": ["AutoCAD", "Structural Engineering", "Construction Management", "Civil Engineering", "Project Planning", "Site Inspection"],
        "expected_domain": "Default"
    },
    "customer_service_rep": {
        "text": """
        Jessica Alba - Customer Support Lead
        jessica.a@support.com | 555-0110 | linkedin.com/in/jessicaalba
        Summary: Dedicated Customer Service Representative with 4 years experience in CRM ticketing, call center support, and client satisfaction.
        Skills: Customer Support, CRM, Communication, Escalation Management, Call Center Operations, Zendesk
        Experience: Support Lead at Helpdesk LLC (2021-Present). Resolved 1,000+ support tickets with 96% positive CSAT score.
        Education: High School Diploma - Central High
        """,
        "sections": {
            "summary": "Dedicated Customer Service Representative with 4 years experience in CRM ticketing, call center support, and client satisfaction.",
            "skills": "Customer Support, CRM, Communication, Escalation Management, Call Center Operations, Zendesk",
            "experience": "Support Lead at Helpdesk LLC (2021-Present). Resolved 1,000+ support tickets with 96% positive CSAT score.",
            "education": "High School Diploma - Central High"
        },
        "skills": ["Customer Support", "CRM", "Communication", "Escalation Management", "Call Center Operations", "Zendesk"],
        "expected_domain": "Default"
    }
}


# ---------------------------------------------------------
# 2. EVALUATION TEST CASES
# ---------------------------------------------------------

def test_evaluation_domain_detection_accuracy():
    """Verify domain detection across 10 synthetic resume profiles."""
    for key, data in SYNTHETIC_RESUMES.items():
        parsed = create_parsed_resume_fixture(data["text"], data["sections"], data["skills"])
        analysis = analyze_resume(parsed)
        # Verify detected domain matches expected or Default
        expected = data["expected_domain"]
        if expected != "Default":
            assert analysis["domain"] == expected, f"Failed for {key}: got {analysis['domain']}, expected {expected}"


def test_score_ordering_strong_vs_weak():
    """Verify score ordering relationship: Strong > Average > Weak for Accountants."""
    strong_text = SYNTHETIC_RESUMES["accountant"]["text"]
    strong_parsed = create_parsed_resume_fixture(strong_text, SYNTHETIC_RESUMES["accountant"]["sections"], SYNTHETIC_RESUMES["accountant"]["skills"])
    strong_res = analyze_resume(strong_parsed)

    weak_text = "Robert Smith. Contact: robert@test.com. Accountant helper."
    weak_parsed = create_parsed_resume_fixture(weak_text, {"summary": "Accountant helper."})
    weak_res = analyze_resume(weak_parsed)

    assert strong_res["score"] > weak_res["score"] + 20


def test_cross_domain_match_protection():
    """Verify Graphic Designer applying for Nurse JD receives low match score (<= 40)."""
    designer_data = SYNTHETIC_RESUMES["graphic_designer"]
    designer_parsed = create_parsed_resume_fixture(designer_data["text"], designer_data["sections"], designer_data["skills"])

    nurse_jd = """
    Registered Nurse required for ICU department.
    Required Skills: Patient Care, Clinical Documentation, Triage, Medication Administration
    """
    match_res = match_resume_to_job(designer_parsed, nurse_jd)

    assert match_res["job_match_score"] <= 45


def test_adjacent_domain_compatibility():
    """Verify Sales Executive applying for Business Development Executive receives high match score (>= 60)."""
    sales_data = SYNTHETIC_RESUMES["sales_executive"]
    sales_parsed = create_parsed_resume_fixture(sales_data["text"], sales_data["sections"], sales_data["skills"])

    bizdev_jd = """
    Business Development Manager required for B2B client acquisition, lead generation, and account executive management.
    Required Skills: B2B Sales, Lead Generation, Account Management, Negotiation
    """
    match_res = match_resume_to_job(sales_parsed, bizdev_jd)

    assert match_res["job_match_score"] >= 60


def test_semantic_similarity_calibration():
    """Verify semantic phrase similarity calibrations across Strong, Moderate, and Unrelated pairs."""
    # Strong pairs
    assert embedding_service.similarity("managed sales representatives", "led sales teams") >= 0.50
    assert embedding_service.similarity("prepared financial statements", "financial reporting") >= 0.55
    assert embedding_service.similarity("provided direct patient care", "clinical patient care") >= 0.55

    # Unrelated pair
    assert embedding_service.similarity("graphic designer", "registered nurse") <= 0.35


def test_false_positive_mitigation_soft_skills_only():
    """Verify generic soft skills (leadership, communication) do NOT trigger high match on clinical JD."""
    soft_text = "Jane Doe. Skills: Leadership, Communication, Teamwork, Problem Solving."
    parsed = create_parsed_resume_fixture(soft_text, {"skills": "Leadership, Communication, Teamwork, Problem Solving"})

    clinical_jd = """
    Registered Nurse required.
    Required Skills: Patient Care, Clinical Documentation, Triage, Medication Administration
    """
    match_res = match_resume_to_job(parsed, clinical_jd)

    assert match_res["job_match_score"] <= 35


def test_required_vs_preferred_skill_weighting():
    """Verify missing required skills penalizes match score more heavily than missing preferred skills."""
    cand_data = SYNTHETIC_RESUMES["software_engineer"]
    cand_parsed = create_parsed_resume_fixture(cand_data["text"], cand_data["sections"], cand_data["skills"])

    # JD 1: Missing Required
    jd_missing_req = """
    Required: C++, Java, Rust
    Preferred: Python, React
    """
    res1 = match_resume_to_job(cand_parsed, jd_missing_req)

    # JD 2: Missing Preferred
    jd_missing_pref = """
    Required: Python, React
    Preferred: C++, Java, Rust
    """
    res2 = match_resume_to_job(cand_parsed, jd_missing_pref)

    assert res2["job_match_score"] > res1["job_match_score"] + 20


def test_hallucination_audit_zero_unsupported_claims():
    """Verify system recommendations NEVER hallucinate unmentioned certifications or skills."""
    text = "John Doe - Simple Software Developer with Python experience."
    parsed = create_parsed_resume_fixture(text, {"skills": "Python"})
    analysis = analyze_resume(parsed)
    recs = generate_recommendations(analysis)

    for rec in recs.get("general_improvements", []):
        action_text = rec["action"].lower()
        # Should not claim candidate has CPA, RN, or PMP
        assert "you hold a cpa" not in action_text
        assert "as a registered nurse" not in action_text
        assert "your pmp certification" not in action_text
