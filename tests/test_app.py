import io
import os
import shutil
import pytest
import fitz
import docx
from app import create_app
from services.upload_service import allowed_file


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    test_upload_dir = os.path.join(os.path.dirname(__file__), "test_uploads")
    
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "UPLOAD_FOLDER": test_upload_dir,
        "MAX_CONTENT_LENGTH": 1 * 1024 * 1024,  # 1 MB for testing max size limit
    })

    yield app

    # Cleanup test uploads directory after tests complete
    if os.path.exists(test_upload_dir):
        shutil.rmtree(test_upload_dir)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


def generate_pdf_bytes(text_content: str) -> bytes:
    """Helper to generate PDF file bytes in memory."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text_content)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def generate_docx_bytes(text_content: str) -> bytes:
    """Helper to generate DOCX file bytes in memory."""
    doc = docx.Document()
    doc.add_paragraph(text_content)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_allowed_file_helper():
    """Test allowed_file utility function."""
    assert allowed_file("resume.pdf") is True
    assert allowed_file("resume.docx") is True
    assert allowed_file("RESUME.PDF") is True
    assert allowed_file("MY.DOCUMENT.DOCX") is True

    assert allowed_file("resume.txt") is False
    assert allowed_file("resume.png") is False
    assert allowed_file("resume.exe") is False
    assert allowed_file("no_extension") is False
    assert allowed_file("") is False


def test_homepage_loads_successfully(client):
    """Verify homepage (GET /) loads successfully with status 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Resume Analyzer" in response.data
    assert b"Analyze Resume" in response.data or b"Upload Resume" in response.data


def test_upload_valid_pdf_and_render_results(client):
    """Verify uploading a valid PDF parses text, detects sections, extracts skills, analyzes score, and renders result page."""
    pdf_content = "john@example.com\n\nPROFESSIONAL SUMMARY\nJohn Doe - Software Architect\n\nSKILLS\nPython, Flask, Docker"
    pdf_bytes = generate_pdf_bytes(pdf_content)
    data = {
        "resume": (io.BytesIO(pdf_bytes), "sample_resume.pdf")
    }
    response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert b"John Doe - Software Architect" in response.data
    assert b"Quality Score" in response.data or b"Overall Score" in response.data
    assert b"Skill Evidence Analysis" in response.data or b"Evidence Analysis" in response.data


def test_upload_valid_docx_with_job_description_matching(client):
    """Verify uploading a DOCX with job description triggers Phase 6 & 8 job match and evidence matrix."""
    docx_content = "WORK EXPERIENCE\nJane Smith - Python Engineer\n\nSKILLS\nPython, Flask, Docker"
    docx_bytes = generate_docx_bytes(docx_content)
    jd_text = "Required: Python, Flask, Docker, Kubernetes"
    
    data = {
        "resume": (io.BytesIO(docx_bytes), "my_cv.docx"),
        "job_description": jd_text
    }
    response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert b"Job Match Score" in response.data
    assert b"Job Requirement Evidence Matrix" in response.data or b"Evidence Matrix" in response.data


def test_upload_invalid_extension_rejected(client):
    """Verify uploading a file with invalid extension (.txt) is rejected."""
    data = {
        "resume": (io.BytesIO(b"plain text resume"), "resume.txt")
    }
    response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid file extension" in response.data


def test_upload_missing_file_rejected(client):
    """Verify submitting without a file is rejected."""
    response = client.post("/upload", data={}, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert b"No file part in the request" in response.data or b"No file selected" in response.data

    data = {"resume": (io.BytesIO(b""), "")}
    response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert b"No file selected for upload" in response.data


def test_json_api_upload_with_job_description_and_evidence_analysis(client):
    """Verify JSON API upload response contains quality analysis, job match, recommendation plan, and evidence analysis."""
    headers = {"Accept": "application/json"}
    
    pdf_content = "SKILLS\nPython, Flask, PostgreSQL\n\nEDUCATION\nState University"
    pdf_bytes = generate_pdf_bytes(pdf_content)
    jd_text = "Required: Python, Flask\nPreferred: AWS"

    data = {
        "resume": (io.BytesIO(pdf_bytes), "test_api.pdf"),
        "job_description": jd_text
    }
    response = client.post("/upload", data=data, content_type="multipart/form-data", headers=headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert json_data["result"]["job_match"]["has_job_description"] is True
    assert json_data["result"]["job_match"]["job_match_score"] == 80
    assert "recommendation_plan" in json_data["result"]
    assert "evidence_analysis" in json_data["result"]
    assert "evidence_strength_score" in json_data["result"]["evidence_analysis"]
    assert "job_evidence_matrix" in json_data["result"]["evidence_analysis"]
