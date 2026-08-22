import json
import os
import re
from services.nlp import embedding_service
from services.skill_extractor import extract_skills

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "skills")


def load_all_domain_catalogs() -> dict[str, list[str]]:
    """
    Loads domain skill lists from data/skills/*.json files.
    """
    catalogs = {
        "technical_skills": [],
        "tools": [],
        "soft_skills": [],
        "domain_competencies": []
    }

    if not os.path.exists(SKILLS_DIR):
        return catalogs

    for fn in os.listdir(SKILLS_DIR):
        if fn.endswith(".json"):
            fp = os.path.join(SKILLS_DIR, fn)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    skills_list = data.get("skills", [])
                    cat_name = data.get("category", "")

                    if "Soft Skills" in cat_name:
                        catalogs["soft_skills"].extend(skills_list)
                    elif "Tools" in cat_name:
                        catalogs["tools"].extend(skills_list)
                    else:
                        catalogs["technical_skills"].extend(skills_list)
                        catalogs["domain_competencies"].extend(skills_list)
            except Exception:
                pass

    return catalogs


def extract_categorized_skills(resume_text: str, sections: dict = None) -> dict[str, list[str]]:
    """
    Extracts and categorizes skills across technical_skills, tools, soft_skills, and domain_competencies.
    """
    catalogs = load_all_domain_catalogs()
    all_extracted = extract_skills(resume_text)

    categorized = {
        "technical_skills": [],
        "tools": [],
        "soft_skills": [],
        "domain_competencies": []
    }

    soft_set = set(catalogs["soft_skills"])
    tools_set = set(catalogs["tools"])

    for skill in all_extracted:
        if skill in tools_set:
            if skill not in categorized["tools"]:
                categorized["tools"].append(skill)
        elif skill in soft_set:
            if skill not in categorized["soft_skills"]:
                categorized["soft_skills"].append(skill)
        else:
            if skill not in categorized["technical_skills"]:
                categorized["technical_skills"].append(skill)
            if skill not in categorized["domain_competencies"]:
                categorized["domain_competencies"].append(skill)

    # Perform semantic phrase matching for implicit skill evidence
    phrase_mappings = [
        ("managed sales representatives", "Leadership", "soft_skills"),
        ("managed sales team", "Leadership", "soft_skills"),
        ("led sales team", "Team Leadership", "soft_skills"),
        ("handled patient records", "Clinical Documentation", "domain_competencies"),
        ("managed financial statements", "Financial Reporting", "technical_skills"),
        ("reconciled accounts", "Reconciliation", "technical_skills"),
        ("developed lesson plans", "Lesson Planning", "technical_skills"),
    ]

    text_lower = (resume_text or "").lower()
    for phrase, inferred_skill, target_cat in phrase_mappings:
        if phrase in text_lower or embedding_service.similarity(resume_text[:1000] if resume_text else "", phrase) >= 0.65:
            if inferred_skill not in categorized[target_cat]:
                categorized[target_cat].append(inferred_skill)

    return categorized
