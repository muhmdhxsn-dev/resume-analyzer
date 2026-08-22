import io
import os
import shutil
import pytest
import fitz
import docx
from werkzeug.datastructures import FileStorage
from app import create_app
from services.upload_service import process_upload, validate_file_magic


@pytest.fixture
def app_instance():
    """Fixture creating a test app instance."""
    test_upload_dir = os.path.join(os.path.dirname(__file__), "prod_test_uploads")
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "prod-test-secret-key",
        "UPLOAD_FOLDER": test_upload_dir,
        "MAX_CONTENT_LENGTH": 1 * 1024 * 1024,  # 1 MB for size testing
    })
    yield app
    if os.path.exists(test_upload_dir):
        shutil.rmtree(test_upload_dir)


@pytest.fixture
def client(app_instance):
    """Test client."""
    return app_instance.test_client()


def generate_valid_pdf_bytes(text: str = "John Doe Resume\nSkills: Python, Flask") -> bytes:
    """Generates valid PDF bytes with %PDF- header."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def generate_valid_docx_bytes() -> bytes:
    """Generates valid DOCX bytes with PK zip header."""
    doc = docx.Document()
    doc.add_paragraph("Jane Smith Resume\nSkills: Python, Docker")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_magic_header_validation_and_spoof_rejection():
    """Verify magic header validation accepts valid PDF/DOCX and rejects spoofed binary files."""
    valid_pdf_storage = FileStorage(stream=io.BytesIO(generate_valid_pdf_bytes()), filename="valid.pdf")
    is_valid, _ = validate_file_magic(valid_pdf_storage)
    assert is_valid is True

    valid_docx_storage = FileStorage(stream=io.BytesIO(generate_valid_docx_bytes()), filename="valid.docx")
    is_valid, _ = validate_file_magic(valid_docx_storage)
    assert is_valid is True

    # Spoofed file: executable binary content renamed to .pdf
    spoofed_storage = FileStorage(stream=io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00THIS IS AN EXE FILE"), filename="resume.pdf")
    is_valid, msg = validate_file_magic(spoofed_storage)
    assert is_valid is False
    assert "header does not match a valid PDF format" in msg


def test_security_http_headers_present(client):
    """Verify response includes required security HTTP headers."""
    response = client.get("/")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")


def test_temporary_file_cleanup_after_upload(client, app_instance):
    """Verify uploaded file is deleted from uploads directory after processing."""
    pdf_bytes = generate_valid_pdf_bytes()
    data = {
        "resume": (io.BytesIO(pdf_bytes), "my_resume.pdf")
    }
    response = client.post("/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 200

    upload_folder = app_instance.config["UPLOAD_FOLDER"]
    # Verify directory does not contain leftover temp resume files
    leftover_files = [f for f in os.listdir(upload_folder) if f != ".gitkeep"]
    assert len(leftover_files) == 0


def test_job_description_character_length_limit(client):
    """Verify job description exceeding 10,000 characters is rejected."""
    pdf_bytes = generate_valid_pdf_bytes()
    oversized_jd = "Python " * 2000  # 14,000 chars

    data = {
        "resume": (io.BytesIO(pdf_bytes), "resume.pdf"),
        "job_description": oversized_jd
    }
    response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert b"exceeds maximum allowed size" in response.data or b"Job description" in response.data


def test_custom_error_handlers_rendering(client):
    """Verify 404 error handler renders error.html."""
    response = client.get("/nonexistent-page-route")
    assert response.status_code == 404
    assert b"ERROR 404" in response.data or b"Page Not Found" in response.data
    assert b"Return to Upload Page" in response.data


def test_json_error_handlers(client):
    """Verify API requests return JSON error responses instead of HTML."""
    headers = {"Accept": "application/json"}
    response = client.get("/nonexistent-page-route", headers=headers)
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data["success"] is False
    assert "found" in json_data["message"].lower() or "not found" in json_data["message"].lower()


def test_secret_key_loaded_from_config(app_instance):
    """Verify secret key is properly configured from environment/config."""
    assert app_instance.config["SECRET_KEY"] == "prod-test-secret-key"


def test_safe_filename_handling_uuid_prefix():
    """Verify process_upload generates a safe UUID filename that prevents path traversal."""
    file_storage = FileStorage(stream=io.BytesIO(generate_valid_pdf_bytes()), filename="../../dangerous_path.pdf")
    upload_dir = os.path.join(os.path.dirname(__file__), "prod_test_uploads")
    
    success, msg, saved_fn = process_upload(file_storage, upload_dir)

    assert success is True
    assert ".." not in saved_fn
    assert "/" not in saved_fn
    assert "\\" not in saved_fn

    # Cleanup test file
    saved_path = os.path.join(upload_dir, saved_fn)
    if os.path.exists(saved_path):
        os.remove(saved_path)
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)


def test_jinja_xss_autoescaping_in_rendered_output(client):
    """Verify Jinja autoescapes malicious script payload in resume text."""
    malicious_text = "<script>alert('XSS_ATTACK')</script>\nSkills: Python"
    pdf_bytes = generate_valid_pdf_bytes(malicious_text)

    data = {
        "resume": (io.BytesIO(pdf_bytes), "xss_test.pdf")
    }
    response = client.post("/upload", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    # Jinja must escape raw script tags to HTML entities or omit raw script execution
    assert b"<script>alert('XSS_ATTACK')</script>" not in response.data or b"&lt;script&gt;" in response.data


def test_zero_byte_empty_file_rejected(client):
    """Verify zero-byte empty file is rejected with a friendly error message."""
    data = {
        "resume": (io.BytesIO(b""), "empty.pdf")
    }
    response = client.post("/upload", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert b"File is empty" in response.data or b"Invalid" in response.data


def test_health_endpoint_response(client):
    """Verify /health endpoint returns HTTP 200 with status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["nlp"] in ("available", "fallback")


def test_embedding_lru_cache_behavior():
    """Verify embedding service LRU cache hits, misses, and stats tracking."""
    from services.nlp import embedding_service
    embedding_service.clear_cache()

    stats0 = embedding_service.get_cache_stats()
    assert stats0["size"] == 0

    emb1 = embedding_service.embed("test lru query snippet")
    stats1 = embedding_service.get_cache_stats()
    assert stats1["hits"] == 0
    assert stats1["misses"] == 1

    emb2 = embedding_service.embed("test lru query snippet")
    stats2 = embedding_service.get_cache_stats()
    assert stats2["hits"] == 1
    assert emb1 == emb2


def test_vercel_runtime_detection_and_fallback(monkeypatch):
    """Verify VERCEL=1 env var forces lightweight Jaccard fallback mode cleanly."""
    from services.nlp import embedding_service
    embedding_service._MODEL_LOAD_ATTEMPTED = False
    embedding_service._MODEL_INSTANCE = None
    embedding_service._IS_MODEL_AVAILABLE = False

    monkeypatch.setenv("VERCEL", "1")

    assert embedding_service.is_available() is False
    sim = embedding_service.similarity("python developer", "python engineer")
    assert 0.0 <= sim <= 1.0

    embedding_service._MODEL_LOAD_ATTEMPTED = False
    embedding_service._MODEL_INSTANCE = None
    embedding_service._IS_MODEL_AVAILABLE = False


def test_health_endpoint_vercel_fallback(client, monkeypatch):
    """Verify GET /health reports nlp: fallback when VERCEL environment variable is set."""
    from services.nlp import embedding_service
    embedding_service._MODEL_LOAD_ATTEMPTED = False
    embedding_service._MODEL_INSTANCE = None
    embedding_service._IS_MODEL_AVAILABLE = False

    monkeypatch.setenv("VERCEL", "1")

    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["nlp"] == "fallback"

    embedding_service._MODEL_LOAD_ATTEMPTED = False
    embedding_service._MODEL_INSTANCE = None
    embedding_service._IS_MODEL_AVAILABLE = False
