import re
from typing import Dict, List, Optional
from services.skill_extractor import extract_skills
from services.nlp import embedding_service
from services.nlp.domain_detector import detect_domains_and_roles
from services.nlp.semantic_skill_extractor import extract_categorized_skills
from services.evidence_analyzer import normalize_skill, check_skill_in_text

PREFERRED_KEYWORDS = [
    'preferred', 'nice to have', 'nice-to-have', 'plus', 'bonus', 'desired',
    'preferred qualifications', 'optional', 'good to have'
]

REQUIRED_KEYWORDS = [
    'required', 'requirements', 'must have', 'must-have', 'essential',
    'qualifications', 'minimum qualifications', 'what you need', 'what we look for',
    'responsibilities', 'technical skills'
]


def analyze_job_description(jd_text: str) -> dict:
    """
    Parses a Job Description and extracts required vs preferred skills.
    Maintains 100% backward compatibility with Phase 6-11 tests and callers.
    
    Args:
        jd_text (str): Raw text of the job description.
        
    Returns:
        dict: Containing lists for 'required', 'preferred', and 'all_jd_skills'.
    """
    if not jd_text or not jd_text.strip():
        return {"required": [], "preferred": [], "all_jd_skills": []}

    lines = jd_text.split('\n')
    current_classification = "required"

    required_blocks = []
    preferred_blocks = []

    for line in lines:
        raw_line = line.strip()
        if not raw_line:
            continue

        lower_line = raw_line.lower()

        # Check for heading classification cues (short lines <= 60 chars)
        if len(raw_line) <= 60:
            if any(kw in lower_line for kw in PREFERRED_KEYWORDS) and not any(req_kw in lower_line for req_kw in ['required qualifications', 'minimum qualifications']):
                current_classification = "preferred"
            elif any(kw in lower_line for kw in REQUIRED_KEYWORDS):
                current_classification = "required"

        if current_classification == "preferred":
            preferred_blocks.append(raw_line)
        else:
            required_blocks.append(raw_line)

    required_text = "\n".join(required_blocks)
    preferred_text = "\n".join(preferred_blocks)

    extracted_req = extract_skills(required_text)
    extracted_pref = extract_skills(preferred_text)

    # Ensure deduplication: if a skill is required, prioritize required and remove from preferred
    req_set = set(extracted_req)
    final_required = extracted_req
    final_preferred = [s for s in extracted_pref if s not in req_set]

    # Combine all unique skills maintaining order
    all_skills = final_required + [s for s in final_preferred if s not in final_required]

    return {
        "required": final_required,
        "preferred": final_preferred,
        "all_jd_skills": all_skills
    }


def build_job_profile(jd_text: str) -> dict:
    """
    Extracts a normalized, industry-agnostic JobProfile representation from job text.
    
    Args:
        jd_text (str): Raw text of the job description.
        
    Returns:
        dict: Normalized JobProfile dictionary.
    """
    if not jd_text or not jd_text.strip():
        return {
            "title": "",
            "domains": [],
            "required_skills": [],
            "preferred_skills": [],
            "tools": [],
            "soft_skills": [],
            "domain_competencies": [],
            "certifications": [],
            "education": [],
            "responsibilities": [],
            "minimum_years_experience": 0.0
        }

    lines = [l.strip() for l in jd_text.split('\n') if l.strip()]
    inferred_title = lines[0] if lines else "Target Position"

    domains, probable_roles = detect_domains_and_roles(jd_text)
    categorized_skills = extract_categorized_skills(jd_text)
    jd_analysis = analyze_job_description(jd_text)

    # Experience requirement regex
    min_yoe = 0.0
    yoe_match = re.search(r'(\d+)\+?\s*years?(?:\s+of)?\s+experience', jd_text, re.IGNORECASE)
    if yoe_match:
        try:
            min_yoe = float(yoe_match.group(1))
        except ValueError:
            pass

    return {
        "title": inferred_title,
        "domains": domains,
        "probable_roles": probable_roles,
        "required_skills": jd_analysis["required"],
        "preferred_skills": jd_analysis["preferred"],
        "tools": categorized_skills.get("tools", []),
        "soft_skills": categorized_skills.get("soft_skills", []),
        "domain_competencies": categorized_skills.get("domain_competencies", []),
        "certifications": [],
        "education": [],
        "responsibilities": [l for l in lines if len(l) > 30][:10],
        "minimum_years_experience": min_yoe
    }


def _match_skill_hybrid(candidate_skills: set, candidate_text: str, target_skill: str) -> tuple[str, str, float]:
    """
    Evaluates a single job skill against candidate data using hybrid exact + alias + semantic matching.
    
    Returns:
        tuple: (match_level: STRONG|MODERATE|WEAK|MISSING, match_type: Exact|Semantic|None, similarity: float)
    """
    target_norm = normalize_skill(target_skill).lower()

    # 1. Exact Match & Alias Check against candidate skills set
    for cs in candidate_skills:
        if cs.lower() == target_norm or normalize_skill(cs).lower() == target_norm:
            return "STRONG", "Exact", 1.0

    # Check via boundary-aware regex search in candidate text
    if candidate_text and check_skill_in_text(target_skill, candidate_text):
        return "STRONG", "Exact", 1.0

    # 2. Semantic Embedding Similarity Check
    if embedding_service.is_available() and candidate_text:
        sample_snippet = candidate_text[:1000]
        sim = embedding_service.similarity(sample_snippet, target_skill)

        if sim >= 0.70:
            return "STRONG", "Semantic", sim
        elif sim >= 0.55:
            return "MODERATE", "Semantic", sim
        elif sim >= 0.40:
            return "WEAK", "Semantic", sim
        return "MISSING", "None", sim

    return "MISSING", "None", 0.0


def match_resume_to_job(parsed_resume: dict, jd_text: str) -> dict:
    """
    Matches a parsed resume against a job description text using Phase 12 Semantic & Industry-Agnostic Engine.
    Computes explainable score (0 to 100) combining exact/semantic skills, experience, domain alignment, and YoE.
    
    Returns:
        dict: Complete structured job matching results compatible with Phase 6-11 APIs & UI templates.
    """
    if not jd_text or not jd_text.strip():
        return {
            "has_job_description": False,
            "job_match_score": 0,
            "jd_skills": {"required": [], "preferred": []},
            "matched_skills": [],
            "matched_required_skills": [],
            "missing_required_skills": [],
            "matched_preferred_skills": [],
            "missing_preferred_skills": [],
            "evidence": [],
            "recommendations": []
        }

    # Extract Profiles
    job_prof = build_job_profile(jd_text)
    cand_prof = parsed_resume.get("candidate_profile") or {}
    cleaned_text = parsed_resume.get("cleaned_text", "")
    section_skills = set(parsed_resume.get("skills", []))
    full_text_skills = set(extract_skills(cleaned_text))
    candidate_skills_set = section_skills.union(full_text_skills)

    required_jd = job_prof["required_skills"]
    preferred_jd = job_prof["preferred_skills"]
    all_jd_skills = required_jd + [s for s in preferred_jd if s not in required_jd]

    # --- 1. Skill & Competency Matching ---
    matched_required = []
    missing_required = []
    matched_preferred = []
    missing_preferred = []
    evidence_list = []

    for skill in required_jd:
        level, match_type, sim = _match_skill_hybrid(candidate_skills_set, cleaned_text, skill)
        if level in ["STRONG", "MODERATE"]:
            matched_required.append(skill)
        else:
            missing_required.append(skill)

        evidence_list.append({
            "requirement": skill,
            "type": "Required Skill",
            "level": level,
            "match_type": match_type,
            "similarity": sim
        })

    for skill in preferred_jd:
        level, match_type, sim = _match_skill_hybrid(candidate_skills_set, cleaned_text, skill)
        if level in ["STRONG", "MODERATE"]:
            matched_preferred.append(skill)
        else:
            missing_preferred.append(skill)

        evidence_list.append({
            "requirement": skill,
            "type": "Preferred Skill",
            "level": level,
            "match_type": match_type,
            "similarity": sim
        })

    total_req = len(required_jd)
    total_pref = len(preferred_jd)

    # Deterministic 80/20 Skill Ratio Calculation
    if total_req == 0 and total_pref == 0:
        base_score = 0.0
    elif total_pref == 0:
        base_score = 100.0 * len(matched_required) / total_req
    elif total_req == 0:
        base_score = 100.0 * len(matched_preferred) / total_pref
    else:
        req_ratio = len(matched_required) / total_req
        pref_ratio = len(matched_preferred) / total_pref
        base_score = (80.0 * req_ratio) + (20.0 * pref_ratio)

    # --- 2. Cross-Domain Penalty Guard ---
    cand_domains = cand_prof.get("domains", [])
    job_domains = job_prof.get("domains", [])

    if cand_domains and job_domains:
        cand_top = cand_domains[0].get("domain", "")
        job_top = job_domains[0].get("domain", "")
        cand_conf = cand_domains[0].get("confidence", 0.0)
        job_conf = job_domains[0].get("confidence", 0.0)

        # Only apply cross-domain penalty if BOTH domains are strongly detected (confidence >= 0.3) AND distinct
        if cand_conf >= 0.3 and job_conf >= 0.3 and cand_top.lower() != job_top.lower():
            base_score = base_score * 0.4

    final_score = round(base_score)
    final_score = max(0, min(100, int(final_score)))

    # All matched skills list
    all_matched = matched_required + [s for s in matched_preferred if s not in matched_required]

    # Recommendations
    recommendations = []
    if len(all_jd_skills) == 0:
        recommendations.append("No recognized skills from our catalog were detected in the provided job description.")
    else:
        if missing_required:
            recommendations.append(f"Missing required skills: {', '.join(missing_required)}. Consider highlighting these on your resume if experienced.")
        if missing_preferred:
            recommendations.append(f"Missing preferred skills: {', '.join(missing_preferred)}. Adding these can increase your competitive edge.")
        if final_score >= 80:
            recommendations.append("Excellent skill match! Your resume strongly aligns with this job description.")
        elif final_score >= 50:
            recommendations.append("Good skill match with minor gaps in required or preferred skills.")
        else:
            recommendations.append("Low domain or skill alignment with this job description.")

    return {
        "has_job_description": True,
        "job_match_score": final_score,
        "jd_skills": {
            "required": required_jd,
            "preferred": preferred_jd
        },
        "matched_skills": all_matched,
        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "evidence": evidence_list,
        "recommendations": recommendations
    }
