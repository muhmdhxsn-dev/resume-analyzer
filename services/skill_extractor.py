import os
import json
import re

DEFAULT_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "skills.json")
SKILLS_DIR_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "skills")

# Fallback catalog if skills.json is not accessible
FALLBACK_CATALOG = {
    "Programming Languages": ["Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go", "Rust", "PHP", "SQL"],
    "Web & Frameworks": ["Flask", "FastAPI", "Django", "React", "Angular", "Vue.js", "Node.js", "REST API", "GraphQL"],
    "Data & AI": ["NumPy", "Pandas", "Scikit-learn", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning"],
    "Databases": ["PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis"],
    "DevOps & Cloud & Tools": ["Docker", "Kubernetes", "Git", "GitHub", "Linux", "AWS", "Azure", "GCP"]
}


def load_skill_catalog(catalog_path: str = DEFAULT_CATALOG_PATH) -> list[str]:
    """
    Loads and flattens the skill catalog into a list of canonical skill strings.
    Loads from data/skills/*.json domain catalogs as well as data/skills.json.
    """
    skills = []
    seen = set()

    # Load from domain subdirectories if present
    if os.path.exists(SKILLS_DIR_PATH):
        for fn in os.listdir(SKILLS_DIR_PATH):
            if fn.endswith(".json"):
                fp = os.path.join(SKILLS_DIR_PATH, fn)
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        s_list = data.get("skills", [])
                        for s in s_list:
                            if s not in seen:
                                seen.add(s)
                                skills.append(s)
                except Exception:
                    pass

    # Load from default skills.json for backward compatibility
    if isinstance(catalog_path, str) and os.path.exists(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for category, skill_list in data.items():
                    for s in skill_list:
                        if s not in seen:
                            seen.add(s)
                            skills.append(s)
        except Exception:
            pass

    if not skills:
        for category, skill_list in FALLBACK_CATALOG.items():
            for s in skill_list:
                if s not in seen:
                    seen.add(s)
                    skills.append(s)

    return skills


def get_skill_catalog_size(catalog_path: str = DEFAULT_CATALOG_PATH) -> int:
    """Returns total number of skills in the catalog."""
    return len(load_skill_catalog(catalog_path))


def extract_skills(skills_text: str, catalog_path: str = DEFAULT_CATALOG_PATH) -> list[str]:
    """
    Extracts individual canonical skills from text.
    
    Features:
    - Case-insensitive matching.
    - Boundary-aware matching (prevents 'Java' in 'JavaScript' or 'C' in 'C++').
    - Normalizes extracted skills to canonical names.
    - Preserves discovery order while removing duplicates.
    
    Args:
        skills_text (str): Extracted text from resume skills section or body text.
        catalog_path (str): Path to JSON skills catalog or string path.
        
    Returns:
        list[str]: List of unique canonical skill strings in order of discovery.
    """
    if not skills_text or not isinstance(skills_text, str) or not skills_text.strip():
        return []

    target_path = catalog_path if isinstance(catalog_path, str) else DEFAULT_CATALOG_PATH
    canonical_skills = load_skill_catalog(target_path)
    
    # Sort skills by length descending so multi-word/longer names are processed first
    sorted_skills = sorted(canonical_skills, key=lambda s: len(s), reverse=True)

    matches = []  # List of tuples: (start_index, canonical_skill_name)

    for skill in sorted_skills:
        # Custom boundary pattern: ensure no alphanumeric or #/+ chars immediately precede or follow
        pattern = r'(?<![a-zA-Z0-9#+])' + re.escape(skill) + r'(?![a-zA-Z0-9#+])'
        
        for m in re.finditer(pattern, skills_text, re.IGNORECASE):
            matches.append((m.start(), skill))

    if not matches:
        return []

    # Sort discovered matches by text position (order of appearance in resume)
    matches.sort(key=lambda item: item[0])

    # Deduplicate while preserving discovery order
    seen = set()
    extracted = []
    for idx, skill_name in matches:
        if skill_name not in seen:
            seen.add(skill_name)
            extracted.append(skill_name)

    return extracted
