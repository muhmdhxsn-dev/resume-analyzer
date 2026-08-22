import re
from services.nlp.domain_detector import detect_domains_and_roles
from services.nlp.semantic_skill_extractor import extract_categorized_skills
from services.skill_extractor import extract_skills


def estimate_years_of_experience(cleaned_text: str) -> float:
    """
    Estimates total years of experience from dates/years mentioned in the resume.
    """
    if not cleaned_text:
        return 0.0

    years = re.findall(r'\b(19\d{2}|20\d{2})\b', cleaned_text)
    if len(years) >= 2:
        valid_years = [int(y) for y in years if 1980 <= int(y) <= 2030]
        if len(valid_years) >= 2:
            span = max(valid_years) - min(valid_years)
            return round(float(min(30, max(1, span))), 1)

    # Keyword regex estimate
    exp_match = re.search(r'(\d+)\+?\s*years?(?:\s+of)?\s+experience', cleaned_text, re.IGNORECASE)
    if exp_match:
        try:
            return float(exp_match.group(1))
        except ValueError:
            pass

    return 2.0  # Reasonable baseline estimate if text contains work history


def build_candidate_profile(parsed_resume: dict) -> dict:
    """
    Constructs a normalized, domain-agnostic internal CandidateProfile representation.
    
    Args:
        parsed_resume (dict): Output from parse_resume().
        
    Returns:
        dict: Normalized CandidateProfile object.
    """
    cleaned_text = parsed_resume.get("cleaned_text", "")
    sections = parsed_resume.get("sections", {})
    all_skills = parsed_resume.get("skills", []) or extract_skills(cleaned_text)

    domains, probable_roles = detect_domains_and_roles(cleaned_text, sections)
    categorized_skills = extract_categorized_skills(cleaned_text, sections)

    # Flatten skills across all categories
    combined_skills = set(all_skills)
    for cat_list in categorized_skills.values():
        combined_skills.update(cat_list)

    yoe = estimate_years_of_experience(cleaned_text)

    # Educational degree mentions
    edu_text = sections.get("education", "")
    has_degree = bool(edu_text.strip())

    return {
        "domains": domains,
        "probable_roles": probable_roles,
        "skills": sorted(list(combined_skills)),
        "categorized_skills": categorized_skills,
        "years_of_experience": yoe,
        "has_education": has_degree,
        "has_certifications": bool(sections.get("certifications", "").strip()),
        "has_summary": bool(sections.get("summary", "").strip()),
        "summary_snippet": sections.get("summary", "")[:280]
    }
