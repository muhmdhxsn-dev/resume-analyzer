import re

# Canonical section names supported by the analyzer
CANONICAL_SECTIONS = [
    "summary",
    "skills",
    "experience",
    "education",
    "projects",
    "certifications"
]

# Aliases mapping to canonical section names
SECTION_ALIASES = {
    "summary": [
        "summary",
        "profile",
        "professional summary",
        "professional profile",
        "about me",
        "summary of qualifications",
        "executive summary",
        "personal summary",
        "career summary",
        "overview",
        "career objective",
        "objective"
    ],
    "skills": [
        "skills",
        "technical skills",
        "technical skills & tools",
        "technical skills and tools",
        "core skills",
        "core competencies",
        "skills & technologies",
        "skills and technologies",
        "technologies",
        "technical proficiencies",
        "key skills",
        "areas of expertise",
        "competencies",
        "technical background"
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "career history",
        "relevant experience",
        "employment",
        "work summary",
        "experience overview"
    ],
    "education": [
        "education",
        "academic background",
        "academic qualifications",
        "educational background",
        "education and training",
        "academic history",
        "education & qualifications"
    ],
    "projects": [
        "projects",
        "personal projects",
        "academic projects",
        "selected projects",
        "project experience",
        "key projects"
    ],
    "certifications": [
        "certifications",
        "certificates",
        "professional certifications",
        "licenses & certifications",
        "certifications & licenses",
        "licenses and certifications",
        "certifications and licenses"
    ]
}


def match_section_header(line: str) -> str | None:
    """
    Checks if a line of text matches a known resume section heading alias.
    
    Criteria:
    - Must be a reasonably short line (<= 60 chars and <= 6 words).
    - Case-insensitive matching.
    - Tolerant of surrounding punctuation (:, -, *, #, [], (), _, =, |, etc.).
    - Tolerant of extra internal whitespace.
    
    Returns:
        str | None: The canonical section name if matched, or None.
    """
    if not line or not line.strip():
        return None

    raw_line = line.strip()

    # Rule 1: Length guard to avoid misclassifying long ordinary sentences
    if len(raw_line) > 60 or len(raw_line.split()) > 6:
        return None

    # Rule 2: Strip leading/trailing common heading decorations & colons
    cleaned = re.sub(r'^[\s:\-*#_=\[\({|~•>]+|[\s:\-*#_=\]\)}|~•>]+$', '', raw_line)
    
    # Rule 3: Normalize internal whitespace to single spaces and lowercase
    normalized = re.sub(r'\s+', ' ', cleaned).strip().lower()

    if not normalized:
        return None

    # Rule 4: Match against alias dictionary
    for canonical, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return canonical

    return None


def detect_sections(cleaned_text: str) -> dict[str, str]:
    """
    Processes cleaned resume text line-by-line and groups content into
    recognized canonical sections: summary, skills, experience, education,
    projects, and certifications.
    
    Args:
        cleaned_text (str): Cleaned, normalized resume text.
        
    Returns:
        dict[str, str]: Dictionary mapping canonical section names to extracted text.
                        All 6 canonical sections are guaranteed to be present as keys.
    """
    sections: dict[str, list[str]] = {section: [] for section in CANONICAL_SECTIONS}

    if not cleaned_text:
        return {section: "" for section in CANONICAL_SECTIONS}

    lines = cleaned_text.split('\n')
    current_section = None

    for line in lines:
        matched = match_section_header(line)

        if matched:
            current_section = matched
        else:
            # If text appears before any explicit header, default to summary
            if current_section is None:
                if line.strip():
                    current_section = "summary"
                    sections[current_section].append(line)
            else:
                sections[current_section].append(line)

    # Join lines for each section and trim trailing/leading blank lines
    result = {}
    for section in CANONICAL_SECTIONS:
        joined_text = "\n".join(sections[section]).strip()
        result[section] = joined_text

    return result
