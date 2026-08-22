import re
from services.skill_extractor import extract_skills

# Centralized Default category max scores (Total = 100)
DEFAULT_CATEGORY_WEIGHTS = {
    "contact_information": 10,
    "summary": 10,
    "skills": 20,
    "experience": 25,
    "projects": 15,
    "education": 10,
    "certifications": 5,
    "length": 5,
}

# Alias for backward compatibility with legacy tests
CATEGORY_WEIGHTS = DEFAULT_CATEGORY_WEIGHTS

# Domain-Adaptive Scoring Profiles (Total weight = 100 for each profile)
DOMAIN_PROFILES = {
    "Software Engineering & IT": {
        "contact_information": 10,
        "summary": 10,
        "skills": 20,
        "experience": 25,
        "projects": 15,
        "education": 10,
        "certifications": 5,
        "length": 5,
    },
    "Finance & Accounting": {
        "contact_information": 10,
        "summary": 10,
        "skills": 25,
        "experience": 35,
        "projects": 0,
        "education": 10,
        "certifications": 5,
        "length": 5,
    },
    "Marketing & Sales": {
        "contact_information": 10,
        "summary": 10,
        "skills": 25,
        "experience": 35,
        "projects": 0,
        "education": 10,
        "certifications": 5,
        "length": 5,
    },
    "Healthcare & Medicine": {
        "contact_information": 10,
        "summary": 10,
        "skills": 25,
        "experience": 35,
        "projects": 0,
        "education": 10,
        "certifications": 5,
        "length": 5,
    },
    "Education & Teaching": {
        "contact_information": 10,
        "summary": 10,
        "skills": 25,
        "experience": 35,
        "projects": 0,
        "education": 10,
        "certifications": 5,
        "length": 5,
    },
    "Human Resources & Administration": {
        "contact_information": 10,
        "summary": 10,
        "skills": 25,
        "experience": 35,
        "projects": 0,
        "education": 10,
        "certifications": 5,
        "length": 5,
    },
    "Human Resources & Admin": {
        "contact_information": 10,
        "summary": 10,
        "skills": 25,
        "experience": 35,
        "projects": 0,
        "education": 10,
        "certifications": 5,
        "length": 5,
    },
    "Default": DEFAULT_CATEGORY_WEIGHTS
}

# Regex patterns for contact information detection
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
PHONE_REGEX = r'(?:phone|mobile|cell|tel|fax|call)?[\s:]*(?:\+?\d{1,4}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?){1,3}\d{3,4}|\+?\d{7,15}'
LINKEDIN_REGEX = r'linkedin\.com(?:/in/[a-zA-Z0-9_-]+)?|linkedin'
GITHUB_REGEX = r'github\.com(?:/[a-zA-Z0-9_-]+)?|github'

# Action verbs for experience & project scoring
ACTION_VERBS = {
    'developed', 'built', 'created', 'implemented', 'managed', 'designed',
    'optimized', 'maintained', 'deployed', 'tested', 'led', 'improved',
    'spearheaded', 'architected', 'automated', 'engineered', 'launched',
    'delivered', 'integrated', 'configured', 'established', 'revamped',
    'generated', 'increased', 'reduced', 'saved', 'exceeded', 'grew', 'expanded'
}

# Role/Title indicators for summary scoring
ROLE_TITLES = {
    'developer', 'engineer', 'architect', 'analyst', 'designer', 'manager',
    'lead', 'consultant', 'specialist', 'administrator', 'intern', 'programmer',
    'accountant', 'auditor', 'nurse', 'teacher', 'educator', 'recruiter', 'executive'
}

# Degree terminology for education scoring
DEGREE_TERMS = {
    'bs', 'bachelor', 'bachelors', 'ms', 'master', 'masters', 'bsc', 'msc',
    'phd', 'b.s.', 'm.s.', 'b.a.', 'm.a.', 'b.e.', 'b.tech', 'm.tech',
    'computer science', 'engineering', 'degree', 'accounting', 'nursing', 'education', 'commerce'
}

# Institution indicators for education scoring
INSTITUTION_TERMS = {
    'university', 'college', 'institute', 'school', 'academy', 'polytechnic'
}

# Metrics & Impact Regex Patterns
METRIC_REGEX = r'%\s*|\b\d+(?:\.\d+)?\b|\$|€|£|\b(?:percent|users|requests|performance|growth|reduced|increased|saved|revenue|sales|patients|students|team|quota|accounts|volume)\b'
ACHIEVEMENT_IMPACT_REGEX = r'\b(?:increased|reduced|saved|generated|grew|exceeded|improved|delivered|achieved|expanded|managed|led)\b.*?(?:%\s*|\$\s*[\d.]+[MkBk]?|\b\d+\+?\b)'


def extract_features(parsed_resume: dict) -> dict:
    """
    Extracts structured feature flags, metrics, and achievement indicators from parsed resume.
    """
    cleaned_text = parsed_resume.get("cleaned_text", "")
    sections = parsed_resume.get("sections", {})
    extracted_skills = parsed_resume.get("skills", [])
    page_count = parsed_resume.get("page_count")

    # 1. Contact Info
    has_email = bool(re.search(EMAIL_REGEX, cleaned_text, re.IGNORECASE))
    has_phone = bool(re.search(PHONE_REGEX, cleaned_text, re.IGNORECASE))
    has_linkedin = bool(re.search(LINKEDIN_REGEX, cleaned_text, re.IGNORECASE))
    has_github = bool(re.search(GITHUB_REGEX, cleaned_text, re.IGNORECASE))

    # 2. Summary
    summary_text = sections.get("summary", "")
    has_summary = bool(summary_text.strip())
    summary_words = summary_text.split()
    summary_word_count = len(summary_words)
    summary_lower = summary_text.lower()
    summary_has_skill = bool(extract_skills(summary_text))
    summary_has_role = any(role in summary_lower for role in ROLE_TITLES)

    # 3. Skills
    skill_count = len(extracted_skills)

    # 4. Experience & Achievement Analysis
    exp_text = sections.get("experience", "")
    has_experience = bool(exp_text.strip())
    exp_words = exp_text.split()
    experience_word_count = len(exp_words)
    exp_lower = exp_text.lower()
    exp_words_set = set(re.findall(r'\b[a-z]+\b', exp_lower))
    experience_has_action_verb = bool(exp_words_set.intersection(ACTION_VERBS))
    experience_has_metric = bool(re.search(METRIC_REGEX, exp_text, re.IGNORECASE))

    # Measurable Achievements Extraction
    achievements = []
    lines = [l.strip() for l in cleaned_text.split('\n') if l.strip()]
    for line in lines:
        if re.search(ACHIEVEMENT_IMPACT_REGEX, line, re.IGNORECASE):
            achievements.append(line)

    has_achievements = len(achievements) > 0

    # 5. Projects
    proj_text = sections.get("projects", "")
    has_projects = bool(proj_text.strip())
    proj_words = proj_text.split()
    projects_word_count = len(proj_words)
    proj_lower = proj_text.lower()
    proj_words_set = set(re.findall(r'\b[a-z]+\b', proj_lower))
    projects_has_skill = bool(extract_skills(proj_text))
    projects_has_action_verb = bool(proj_words_set.intersection(ACTION_VERBS))
    projects_has_metric_or_detail = bool(re.search(METRIC_REGEX, proj_text, re.IGNORECASE)) or len(proj_words) >= 20

    # 6. Education
    edu_text = sections.get("education", "")
    has_education = bool(edu_text.strip())
    edu_lower = edu_text.lower()
    education_has_degree = any(term in edu_lower for term in DEGREE_TERMS)
    education_has_institution = any(term in edu_lower for term in INSTITUTION_TERMS)

    # 7. Certifications
    cert_text = sections.get("certifications", "")
    has_certifications = bool(cert_text.strip())
    certifications_has_item = len(cert_text.strip()) >= 5

    # 8. Length & Total Words
    total_word_count = len(cleaned_text.split())

    return {
        "has_text": bool(cleaned_text.strip()),
        "has_email": has_email,
        "has_phone": has_phone,
        "has_linkedin": has_linkedin,
        "has_github": has_github,
        "has_summary": has_summary,
        "summary_word_count": summary_word_count,
        "summary_has_skill": summary_has_skill,
        "summary_has_role": summary_has_role,
        "skill_count": skill_count,
        "has_experience": has_experience,
        "experience_word_count": experience_word_count,
        "experience_has_action_verb": experience_has_action_verb,
        "experience_has_metric": experience_has_metric,
        "has_achievements": has_achievements,
        "achievements_list": achievements[:5],
        "has_projects": has_projects,
        "projects_word_count": projects_word_count,
        "projects_has_skill": projects_has_skill,
        "projects_has_action_verb": projects_has_action_verb,
        "projects_has_metric_or_detail": projects_has_metric_or_detail,
        "has_education": has_education,
        "education_has_degree": education_has_degree,
        "education_has_institution": education_has_institution,
        "has_certifications": has_certifications,
        "certifications_has_item": certifications_has_item,
        "page_count": page_count,
        "total_word_count": total_word_count,
    }


def select_scoring_profile(parsed_resume: dict) -> tuple[str, dict]:
    """
    Selects active domain scoring profile based on CandidateProfile.
    
    Returns:
        tuple: (active_domain_name, active_weights_dict)
    """
    cand_prof = parsed_resume.get("candidate_profile")
    if not cand_prof and parsed_resume.get("cleaned_text"):
        try:
            from services.candidate_profile import build_candidate_profile
            cand_prof = build_candidate_profile(parsed_resume)
            parsed_resume["candidate_profile"] = cand_prof
        except Exception:
            cand_prof = {}

    domains = (cand_prof or {}).get("domains", [])

    if domains:
        top_domain = domains[0].get("domain", "")
        top_conf = domains[0].get("confidence", 0.0)

        if top_conf >= 0.25 and top_domain in DOMAIN_PROFILES:
            return top_domain, DOMAIN_PROFILES[top_domain]

    return "Default", DEFAULT_CATEGORY_WEIGHTS


def calculate_scores(features: dict, active_weights: dict = DEFAULT_CATEGORY_WEIGHTS) -> tuple[dict, int]:
    """
    Calculates category scores and total overall score out of 100 based on active profile weights.
    
    Returns:
        tuple: (categories_dict, overall_score)
    """
    categories = {}

    # 1. Contact Info
    c_max = active_weights.get("contact_information", 10)
    contact_score = 0.0
    if features["has_email"]:
        contact_score += 4.0
    if features["has_phone"]:
        contact_score += 3.0
    if features["has_linkedin"]:
        contact_score += 1.5
    if features["has_github"]:
        contact_score += 1.5
    contact_score = min(contact_score, c_max)
    categories["contact_information"] = {
        "score": round(contact_score, 1),
        "max_score": c_max
    }

    # 2. Summary
    s_max = active_weights.get("summary", 10)
    summary_score = 0.0
    if features["has_summary"]:
        summary_score += 4.0
        if features["summary_word_count"] >= 20:
            summary_score += 2.0
        if features["summary_has_skill"]:
            summary_score += 2.0
        if features["summary_has_role"]:
            summary_score += 2.0
    summary_score = min(summary_score, s_max)
    categories["summary"] = {
        "score": round(summary_score, 1),
        "max_score": s_max
    }

    # 3. Skills
    sk_max = active_weights.get("skills", 20)
    count = features["skill_count"]
    if count == 0:
        skills_ratio = 0.0
    elif 1 <= count <= 2:
        skills_ratio = 0.25
    elif 3 <= count <= 4:
        skills_ratio = 0.50
    elif 5 <= count <= 7:
        skills_ratio = 0.75
    else:
        skills_ratio = 1.0
    skills_score = min(sk_max * skills_ratio, sk_max)
    categories["skills"] = {
        "score": round(skills_score, 1),
        "max_score": sk_max
    }

    # 4. Experience & Achievement Boost
    e_max = active_weights.get("experience", 25)
    exp_score = 0.0
    if features["has_experience"]:
        exp_score += e_max * 0.35
        if features["experience_word_count"] >= 30:
            exp_score += e_max * 0.20
        if features["experience_has_action_verb"]:
            exp_score += e_max * 0.25
        if features["experience_has_metric"]:
            exp_score += e_max * 0.20
        if features["has_achievements"]:
            exp_score += e_max * 0.10  # Extra achievement boost!
    exp_score = min(exp_score, e_max)
    categories["experience"] = {
        "score": round(exp_score, 1),
        "max_score": e_max
    }

    # 5. Projects (Optional for non-tech profiles!)
    p_max = active_weights.get("projects", 0)
    if p_max > 0:
        proj_score = 0.0
        if features["has_projects"]:
            proj_score += p_max * 0.35
            if features["projects_word_count"] >= 30:
                proj_score += p_max * 0.20
            if features["projects_has_skill"]:
                proj_score += p_max * 0.20
            if features["projects_has_action_verb"]:
                proj_score += p_max * 0.15
            if features["projects_has_metric_or_detail"]:
                proj_score += p_max * 0.10
        proj_score = min(proj_score, p_max)
        categories["projects"] = {
            "score": round(proj_score, 1),
            "max_score": p_max
        }
    else:
        categories["projects"] = {
            "score": 0.0,
            "max_score": 0
        }

    # 6. Education
    ed_max = active_weights.get("education", 10)
    edu_score = 0.0
    if features["has_education"]:
        edu_score += ed_max * 0.50
        if features["education_has_degree"]:
            edu_score += ed_max * 0.30
        if features["education_has_institution"]:
            edu_score += ed_max * 0.20
    edu_score = min(edu_score, ed_max)
    categories["education"] = {
        "score": round(edu_score, 1),
        "max_score": ed_max
    }

    # 7. Certifications
    ct_max = active_weights.get("certifications", 5)
    cert_score = 0.0
    if features["has_certifications"]:
        cert_score += ct_max * 0.60
        if features["certifications_has_item"]:
            cert_score += ct_max * 0.40
    cert_score = min(cert_score, ct_max)
    categories["certifications"] = {
        "score": round(cert_score, 1),
        "max_score": ct_max
    }

    # 8. Length
    l_max = active_weights.get("length", 5)
    page_count = features["page_count"]
    words = features["total_word_count"]

    if not features["has_text"] or words == 0:
        len_score = 0.0
    elif page_count is not None:
        if page_count in (1, 2):
            len_score = l_max
        elif page_count == 3:
            len_score = l_max * 0.6
        else:
            len_score = l_max * 0.2
    else:
        if words <= 600:
            len_score = l_max
        elif words <= 1200:
            len_score = l_max * 0.6
        else:
            len_score = l_max * 0.2

    len_score = min(len_score, l_max)
    categories["length"] = {
        "score": round(len_score, 1),
        "max_score": l_max
    }

    # Total Overall Score Calculation (bounded [0, 100])
    raw_total = sum(cat["score"] for cat in categories.values())
    total_score = max(0, min(100, int(round(raw_total))))

    return categories, total_score


def generate_feedback(features: dict, categories: dict, active_domain: str = "Default") -> tuple[list[str], list[str], list[str]]:
    """
    Generates domain-aware explainable feedback (strengths, warnings, recommendations).
    """
    strengths = []
    warnings = []
    recommendations = []

    # 1. Contact Information Feedback
    if features["has_email"] and features["has_phone"] and features["has_linkedin"] and features["has_github"]:
        strengths.append("Complete contact information provided (Email, Phone, LinkedIn, and GitHub).")
    elif features["has_email"] and features["has_phone"]:
        strengths.append("Essential contact details (Email and Phone) are present.")
    
    if not features["has_linkedin"]:
        warnings.append("No LinkedIn profile link detected.")
        recommendations.append("Add a LinkedIn profile URL to enhance your professional visibility.")

    if active_domain == "Software Engineering & IT" and not features["has_github"]:
        warnings.append("No GitHub profile link detected.")
        recommendations.append("Add a GitHub profile URL if you have relevant software projects.")

    # 2. Summary Feedback
    if features["has_summary"]:
        if features["summary_word_count"] >= 20 and features["summary_has_role"]:
            strengths.append("Well-structured professional summary with a clear target role.")
    else:
        warnings.append("No professional summary section detected.")
        recommendations.append("Consider adding a 2-3 sentence professional summary highlighting your background.")

    # 3. Skills Feedback
    sc = features["skill_count"]
    if sc >= 8:
        strengths.append(f"Strong technical skill coverage with {sc} recognized skills from the catalog.")
    elif sc >= 4:
        strengths.append(f"Good skill coverage with {sc} recognized technical skills.")
    elif sc < 3:
        warnings.append(f"Low recognized skill count ({sc} skills detected).")
        recommendations.append("Add more industry-standard technical skills, frameworks, and tools to your skills section.")

    # 4. Experience & Achievements Feedback
    if features["has_experience"]:
        if features["experience_has_action_verb"] and (features["experience_has_metric"] or features["has_achievements"]):
            strengths.append("Work experience section contains strong action verbs and quantified achievement metrics.")
        elif features["experience_has_action_verb"]:
            strengths.append("Work experience section effectively uses action verbs.")
        
        if not features["experience_has_metric"] and not features["has_achievements"]:
            warnings.append("Work experience section lacks measurable results or metrics.")
            if active_domain == "Finance & Accounting":
                recommendations.append("Quantify financial impact, cost savings, budget scale, or reporting volume in your experience bullet points.")
            elif active_domain == "Education & Teaching":
                recommendations.append("Highlight measurable student outcomes, class performance improvements, or curriculum achievements.")
            elif active_domain == "Healthcare & Medicine":
                recommendations.append("Include patient volume, clinical metrics, or care quality improvements in your work history.")
            elif active_domain == "Marketing & Sales":
                recommendations.append("Add revenue growth percentages, conversion rates, sales quotas, or campaign ROI metrics.")
            else:
                recommendations.append("Include quantified results (e.g., percentages, metrics, time saved) in your experience bullet points.")
    else:
        warnings.append("No work experience section detected.")

    # 5. Projects Feedback (Only warn for tech profile or default!)
    if features["has_projects"]:
        strengths.append("Resume documents relevant project experience.")
    elif active_domain in ("Software Engineering & IT", "Default"):
        warnings.append("No dedicated projects section detected.")
        recommendations.append("Add a projects section detailing key personal or academic software projects.")

    # 6. Education Feedback
    if features["has_education"] and features["education_has_degree"]:
        strengths.append("Clear educational background with degree qualifications.")

    # 7. Certifications Feedback
    if features["has_certifications"]:
        strengths.append("Certifications section present providing validated credentials.")

    # 8. Length Feedback
    pc = features["page_count"]
    if pc and pc > 3:
        warnings.append(f"Resume is {pc} pages long, which may be too lengthy for recruiters.")
        recommendations.append("Condense your resume to 1-2 pages for maximum readability.")

    return strengths, warnings, recommendations


def analyze_resume(parsed_resume: dict) -> dict:
    """
    Main entrypoint for Phase 13 Adaptive Resume Analysis.
    
    Args:
        parsed_resume (dict): Output from parse_resume().
        
    Returns:
        dict: Complete structured analysis with score out of 100, domain profile, category breakdown,
              strengths, warnings, and recommendations.
    """
    active_domain, active_weights = select_scoring_profile(parsed_resume)
    features = extract_features(parsed_resume)
    categories, total_score = calculate_scores(features, active_weights)
    strengths, warnings, recommendations = generate_feedback(features, categories, active_domain)

    return {
        "score": total_score,
        "max_score": 100,
        "domain": active_domain,
        "categories": categories,
        "strengths": strengths,
        "warnings": warnings,
        "recommendations": recommendations,
        "achievements": features.get("achievements_list", []),
        "features": features
    }
