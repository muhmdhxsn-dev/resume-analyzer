import re
from typing import Dict, List, Optional
from services.skill_extractor import load_skill_catalog, extract_skills

# Alias mapping dictionary resolving common variations to canonical catalog names
SKILL_ALIASES = {
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "psql": "PostgreSQL",
    "restful apis": "REST API",
    "restful api": "REST API",
    "rest apis": "REST API",
    "rest api": "REST API",
    "react.js": "React",
    "reactjs": "React",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "node": "Node.js",
    "nodejs": "Node.js",
    "express": "Express.js",
    "expressjs": "Express.js",
    "nextjs": "Next.js",
    "nuxt": "Nuxt.js",
    "nuxtjs": "Nuxt.js",
    "k8s": "Kubernetes",
    "amazon web services": "AWS",
    "google cloud platform": "GCP",
    "google cloud": "GCP",
    "microsoft azure": "Azure",
    "ci/cd": "CI/CD",
    "continuous integration": "CI/CD",
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "nlp": "Natural Language Processing",
    "cv": "Computer Vision",
    "search engine optimization": "SEO",
    "search engine marketing": "SEM",
    "financial statement preparation": "Financial Reporting",
    "financial reporting": "Financial Reporting",
    "direct patient care": "Patient Care",
    "clinical patient care": "Patient Care",
    "lesson plan": "Lesson Planning",
    "curriculum planning": "Curriculum Development"
}

# Score weights for overall Evidence Strength Metric
EVIDENCE_SCORES = {
    "STRONG": 100,
    "MODERATE": 70,
    "WEAK": 40,
    "MISSING": 0
}


def normalize_skill(skill_name: str) -> str:
    """
    Normalizes a skill string to its canonical representation using explicit alias mapping
    or catalog matching. Preserves distinction between different technologies.
    
    Args:
        skill_name (str): Raw skill name.
        
    Returns:
        str: Normalized canonical skill name.
    """
    if not skill_name or not skill_name.strip():
        return ""

    raw_clean = skill_name.strip()
    lower_name = raw_clean.lower()

    # 1. Check explicit alias dictionary
    if lower_name in SKILL_ALIASES:
        return SKILL_ALIASES[lower_name]

    # 2. Check canonical catalog case-insensitively
    catalog = load_skill_catalog()
    for item in catalog:
        if item.lower() == lower_name:
            return item

    return raw_clean


def check_skill_in_text(skill_name: str, text: str) -> bool:
    """
    Checks if a skill or any of its known aliases appear in the target text block
    using boundary-aware regex.
    
    Args:
        skill_name (str): Skill to search for.
        text (str): Text block to search within.
        
    Returns:
        bool: True if skill or alias is found in text.
    """
    if not skill_name or not text or not text.strip():
        return False

    canonical = normalize_skill(skill_name)
    
    # Collect variants to search (canonical name + aliases)
    variants = [canonical]
    for alias, can_name in SKILL_ALIASES.items():
        if can_name.lower() == canonical.lower() and alias.lower() not in [v.lower() for v in variants]:
            variants.append(alias)

    # Search each variant using boundary matching
    for variant in variants:
        pattern = r'(?<![a-zA-Z0-9#+])' + re.escape(variant) + r'(?![a-zA-Z0-9#+])'
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def analyze_skill_locations(skill_name: str, sections: dict) -> dict:
    """
    Determines all canonical sections in which a skill or its aliases appear.
    
    Returns:
        dict: containing 'in_skills_section', 'in_experience', 'in_projects', and 'locations' list.
    """
    locations = []
    if not sections:
        return {"in_skills_section": False, "in_experience": False, "in_projects": False, "locations": []}

    in_skills_section = check_skill_in_text(skill_name, sections.get("skills", ""))
    in_experience = check_skill_in_text(skill_name, sections.get("experience", ""))
    in_projects = check_skill_in_text(skill_name, sections.get("projects", ""))

    for sec_name, sec_text in sections.items():
        if sec_text and check_skill_in_text(skill_name, sec_text):
            locations.append(sec_name)

    return {
        "in_skills_section": in_skills_section,
        "in_experience": in_experience,
        "in_projects": in_projects,
        "locations": locations
    }


def get_skill_locations(skill_name: str, sections: dict) -> list[str]:
    """Helper returning list of location section names."""
    res = analyze_skill_locations(skill_name, sections)
    return res["locations"]


def evaluate_evidence_strength(in_skills: bool, in_exp: bool, in_proj: bool, locations: list = None) -> str:
    """
    Evaluates evidence strength level (STRONG, MODERATE, WEAK, MISSING).
    Rules:
    - in_skills AND in_exp -> STRONG
    - in_exp AND in_proj -> STRONG
    - in_skills AND in_proj -> MODERATE
    - in_exp ONLY -> MODERATE
    - in_skills ONLY -> WEAK
    - None -> MISSING
    """
    if (in_skills and in_exp) or (in_exp and in_proj):
        return "STRONG"
    elif (in_skills and in_proj) or (in_exp and not in_skills and not in_proj):
        return "MODERATE"
    elif in_skills:
        return "WEAK"
    elif locations and len(locations) > 0:
        return "WEAK"
    else:
        return "MISSING"


def analyze_resume_evidence(parsed_resume: dict, job_match: dict = None, job_match_result: dict = None) -> dict:
    """
    Analyzes skill location context, calculates overall evidence strength score,
    builds Job Evidence Matrix (if JD is provided), and identifies evidence gaps.
    """
    match_data = job_match if job_match is not None else job_match_result

    sections = parsed_resume.get("sections", {})
    cleaned_text = parsed_resume.get("cleaned_text", "")
    resume_skills = parsed_resume.get("skills", [])

    # Extract all skills from resume text
    all_extracted_skills = extract_skills(cleaned_text)
    combined_resume_skills = set(resume_skills).union(set(all_extracted_skills))

    skill_evidence_list = []
    total_score = 0

    for skill in sorted(list(combined_resume_skills)):
        norm_skill = normalize_skill(skill)
        loc_res = analyze_skill_locations(norm_skill, sections)
        strength_level = evaluate_evidence_strength(
            loc_res["in_skills_section"], loc_res["in_experience"], loc_res["in_projects"], loc_res["locations"]
        )
        score = EVIDENCE_SCORES[strength_level]
        
        skill_evidence_list.append({
            "skill": norm_skill,
            "locations": loc_res["locations"],
            "evidence_strength": strength_level,
            "strength_level": strength_level,
            "strength_score": score,
            "reason": f"Skill found in {', '.join(loc_res['locations'])}" if loc_res["locations"] else "Skill missing"
        })
        total_score += score

    avg_evidence_score = round(total_score / max(1, len(skill_evidence_list))) if skill_evidence_list else 0

    # Job Evidence Matrix & Gap Analysis
    job_evidence_matrix = []
    evidence_gaps = []
    matched_count = 0
    total_jd_count = 0

    if match_data and match_data.get("has_job_description"):
        jd_skills = match_data.get("jd_skills", {})
        req_skills = jd_skills.get("required", [])
        pref_skills = jd_skills.get("preferred", [])

        # Process Required Skills
        for skill in req_skills:
            norm_skill = normalize_skill(skill)
            loc_res = analyze_skill_locations(norm_skill, sections)
            strength_level = evaluate_evidence_strength(
                loc_res["in_skills_section"], loc_res["in_experience"], loc_res["in_projects"], loc_res["locations"]
            )
            total_jd_count += 1
            
            is_matched = strength_level != "MISSING"
            if is_matched:
                matched_count += 1

            if is_matched and strength_level == "WEAK":
                evidence_gaps.append({
                    "skill": norm_skill,
                    "type": "Required",
                    "issue": f"Skill {norm_skill} listed in skills/summary but lacks experience context.",
                    "recommendation": f"Add concrete achievements demonstrating {norm_skill} in your experience section if qualified."
                })

            job_evidence_matrix.append({
                "skill": norm_skill,
                "requirement_type": "Required",
                "matched": is_matched,
                "evidence_strength": strength_level,
                "locations": loc_res["locations"],
                "reason": f"Skill evidence strength: {strength_level}"
            })

        # Process Preferred Skills
        for skill in pref_skills:
            norm_skill = normalize_skill(skill)
            loc_res = analyze_skill_locations(norm_skill, sections)
            strength_level = evaluate_evidence_strength(
                loc_res["in_skills_section"], loc_res["in_experience"], loc_res["in_projects"], loc_res["locations"]
            )
            total_jd_count += 1

            is_matched = strength_level != "MISSING"
            if is_matched:
                matched_count += 1

            if is_matched and strength_level == "WEAK":
                evidence_gaps.append({
                    "skill": norm_skill,
                    "type": "Preferred",
                    "issue": f"Preferred skill {norm_skill} lacks experience context.",
                    "recommendation": f"Mention {norm_skill} in work experience to gain competitive advantage."
                })

            job_evidence_matrix.append({
                "skill": norm_skill,
                "requirement_type": "Preferred",
                "matched": is_matched,
                "evidence_strength": strength_level,
                "locations": loc_res["locations"],
                "reason": f"Skill evidence strength: {strength_level}"
            })

    cov_percentage = round((100.0 * matched_count / total_jd_count)) if total_jd_count > 0 else 0

    return {
        "evidence_strength_score": avg_evidence_score,
        "skill_evidence_list": skill_evidence_list,
        "job_evidence_matrix": job_evidence_matrix,
        "evidence_gaps": evidence_gaps,
        "keyword_coverage": {
            "matched": matched_count,
            "total": total_jd_count,
            "percentage": cov_percentage
        },
        "has_job_description": bool(match_data and match_data.get("has_job_description"))
    }
