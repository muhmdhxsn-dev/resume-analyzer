import pytest
from services.section_detector import match_section_header, detect_sections, CANONICAL_SECTIONS


def test_standard_section_headings():
    """Verify exact standard section header matching."""
    assert match_section_header("SUMMARY") == "summary"
    assert match_section_header("SKILLS") == "skills"
    assert match_section_header("EXPERIENCE") == "experience"
    assert match_section_header("EDUCATION") == "education"
    assert match_section_header("PROJECTS") == "projects"
    assert match_section_header("CERTIFICATIONS") == "certifications"


def test_case_insensitive_headings():
    """Verify case-insensitive header matching."""
    assert match_section_header("summary") == "summary"
    assert match_section_header("SkIlLs") == "skills"
    assert match_section_header("Work Experience") == "experience"
    assert match_section_header("Education") == "education"


def test_headings_with_colons_and_punctuation():
    """Verify headings formatted with colons, dashes, hashtags, and brackets."""
    assert match_section_header("TECHNICAL SKILLS:") == "skills"
    assert match_section_header("--- WORK EXPERIENCE ---") == "experience"
    assert match_section_header("### Education:") == "education"
    assert match_section_header("[Projects]") == "projects"
    assert match_section_header("Certifications:") == "certifications"


def test_headings_with_extra_whitespace():
    """Verify headings with leading, trailing, and internal extra whitespace."""
    assert match_section_header("   WORK   EXPERIENCE   ") == "experience"
    assert match_section_header("\tTECHNICAL   SKILLS  :\t") == "skills"
    assert match_section_header("   ACADEMIC   BACKGROUND   ") == "education"


def test_heading_aliases():
    """Verify section alias mappings."""
    # Summary aliases
    assert match_section_header("Professional Profile") == "summary"
    assert match_section_header("About Me") == "summary"

    # Skills aliases
    assert match_section_header("Technical Skills & Tools") == "skills"
    assert match_section_header("Core Competencies") == "skills"
    assert match_section_header("Technologies") == "skills"

    # Experience aliases
    assert match_section_header("Employment History") == "experience"
    assert match_section_header("Career History") == "experience"

    # Education aliases
    assert match_section_header("Academic Qualifications") == "education"
    assert match_section_header("Educational Background") == "education"

    # Projects aliases
    assert match_section_header("Personal Projects") == "projects"
    assert match_section_header("Selected Projects") == "projects"

    # Certifications aliases
    assert match_section_header("Licenses & Certifications") == "certifications"


def test_ordinary_sentences_not_misclassified():
    """Verify ordinary body sentences containing keywords are NOT matched as section headings."""
    sentence_1 = "Developed strong technical skills in Python, Flask, and PostgreSQL over 5 years."
    sentence_2 = "Responsible for managing project experience and client relations."
    sentence_3 = "I have extensive work experience building distributed web services."

    assert match_section_header(sentence_1) is None
    assert match_section_header(sentence_2) is None
    assert match_section_header(sentence_3) is None


def test_multiple_sections_detection():
    """Verify detecting multiple sections in a full resume text and correct content assignment."""
    resume_text = """John Doe
Software Engineer
Email: john@example.com

PROFESSIONAL SUMMARY
Passionate engineer with expertise in Flask and Python.

TECHNICAL SKILLS
Python, Flask, Pytest, SQL, Docker

WORK EXPERIENCE
Senior Developer at Tech Co (2021 - Present)
- Built microservices and web applications.

EDUCATION
B.S. Computer Science, State University

PROJECTS
Resume Analyzer - AI assistant tool

CERTIFICATIONS
AWS Certified Developer
"""

    sections = detect_sections(resume_text)

    assert "John Doe" in sections["summary"]
    assert "Passionate engineer" in sections["summary"]
    assert "Python, Flask, Pytest" in sections["skills"]
    assert "Senior Developer at Tech Co" in sections["experience"]
    assert "B.S. Computer Science" in sections["education"]
    assert "Resume Analyzer" in sections["projects"]
    assert "AWS Certified Developer" in sections["certifications"]


def test_missing_sections():
    """Verify that unpopulated sections return empty strings."""
    resume_text = """SKILLS
Python, SQL

EXPERIENCE
Developer at Company X
"""
    sections = detect_sections(resume_text)

    assert "Python, SQL" in sections["skills"]
    assert "Developer at Company X" in sections["experience"]
    assert sections["summary"] == ""
    assert sections["education"] == ""
    assert sections["projects"] == ""
    assert sections["certifications"] == ""


def test_unknown_sections():
    """Verify that unknown/unrecognized sections do not crash or corrupt standard sections."""
    resume_text = """SUMMARY
Software Engineer

HOBBIES & INTERESTS
Chess, Hiking, Open Source

EXPERIENCE
Developer at Company Y
"""
    sections = detect_sections(resume_text)

    assert "Software Engineer" in sections["summary"]
    assert "Developer at Company Y" in sections["experience"]
    # Unknown section content stays attached to prior section or doesn't crash
    assert isinstance(sections["skills"], str)


def test_empty_text():
    """Verify empty text produces dictionary with empty strings for all 6 sections."""
    sections = detect_sections("")
    for key in CANONICAL_SECTIONS:
        assert key in sections
        assert sections[key] == ""
