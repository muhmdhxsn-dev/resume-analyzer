import pytest
from services.skill_extractor import extract_skills, load_skill_catalog, get_skill_catalog_size


def test_catalog_loading_and_size():
    """Verify catalog loads correctly and has expected size (>50 skills)."""
    catalog = load_skill_catalog()
    assert len(catalog) >= 50
    assert "Python" in catalog
    assert "Flask" in catalog
    assert "Machine Learning" in catalog


def test_comma_separated_skills():
    """Verify extraction from comma-separated skill list."""
    text = "Python, Flask, FastAPI, PostgreSQL"
    skills = extract_skills(text)
    assert skills == ["Python", "Flask", "FastAPI", "PostgreSQL"]


def test_newline_separated_skills():
    """Verify extraction from newline-separated skill list."""
    text = "Python\nFlask\nFastAPI\nDocker"
    skills = extract_skills(text)
    assert skills == ["Python", "Flask", "FastAPI", "Docker"]


def test_pipe_separated_skills():
    """Verify extraction from pipe-separated skill list."""
    text = "Python | Flask | React | AWS"
    skills = extract_skills(text)
    assert skills == ["Python", "Flask", "React", "AWS"]


def test_slash_separated_skills():
    """Verify extraction from slash-separated skill list."""
    text = "Python / Flask / Django / Git"
    skills = extract_skills(text)
    assert skills == ["Python", "Flask", "Django", "Git"]


def test_semicolon_separated_skills():
    """Verify extraction from semicolon-separated skill list."""
    text = "Python; Flask; MongoDB; Redis"
    skills = extract_skills(text)
    assert skills == ["Python", "Flask", "MongoDB", "Redis"]


def test_case_insensitive_matching_and_normalization():
    """Verify case insensitivity and canonical skill name normalization."""
    text = "python, FLASK, fastAPI, postgresql, docker"
    skills = extract_skills(text)
    assert skills == ["Python", "Flask", "FastAPI", "PostgreSQL", "Docker"]


def test_duplicate_removal_preserving_order():
    """Verify duplicate removal while maintaining discovery order."""
    text = "Python, Flask, Python, NumPy, Flask, Docker"
    skills = extract_skills(text)
    assert skills == ["Python", "Flask", "NumPy", "Docker"]


def test_multi_word_skills():
    """Verify multi-word skills are extracted intact."""
    text = "Machine Learning, Deep Learning, REST API, Node.js, Data Science"
    skills = extract_skills(text)
    assert "Machine Learning" in skills
    assert "Deep Learning" in skills
    assert "REST API" in skills
    assert "Node.js" in skills
    assert "Data Science" in skills


def test_substring_false_positives_prevention():
    """Verify that substrings like 'Java' in 'JavaScript' or 'C' in 'C++' are not misidentified."""
    # Scenario A: JavaScript present, standalone Java NOT present
    text_js = "JavaScript, TypeScript, React"
    skills_js = extract_skills(text_js)
    assert "JavaScript" in skills_js
    assert "Java" not in skills_js

    # Scenario B: C++ present, standalone C NOT present
    text_cpp = "C++, C#, Python"
    skills_cpp = extract_skills(text_cpp)
    assert "C++" in skills_cpp
    assert "C#" in skills_cpp
    assert "C" not in skills_cpp

    # Scenario C: Word containing skill name like 'Flasks' or 'Pythons'
    text_word = "Flasks, Pythons"
    skills_word = extract_skills(text_word)
    assert "Flask" not in skills_word
    assert "Python" not in skills_word


def test_unknown_skills_handling():
    """Verify unknown/custom skills are ignored without crashing."""
    text = "Python, CustomInHouseTool, Flask, ProprietaryScript"
    skills = extract_skills(text)
    assert skills == ["Python", "Flask"]


def test_empty_and_no_recognized_skills():
    """Verify empty input and non-matching skills text return empty lists."""
    assert extract_skills("") == []
    assert extract_skills("   ") == []
    assert extract_skills("Some random text with no known software skills") == []
