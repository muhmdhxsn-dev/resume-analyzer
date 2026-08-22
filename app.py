import os
import time
import uuid
import logging
from collections import defaultdict
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv

from services.upload_service import process_upload
from services.resume_parser import parse_resume

# Load environment variables from .env file if available
load_dotenv()

# Configure privacy-conscious logging (no PII or resume body text in log stream)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("resume_analyzer")

# Max Job Description character limit
MAX_JD_LENGTH = 10000

# Simple in-memory rate limiting tracker (IP -> list of timestamps)
UPLOAD_RATE_LIMIT_WINDOW = 60  # seconds
UPLOAD_RATE_LIMIT_MAX = 20     # requests per window
rate_limit_tracker = defaultdict(list)


def is_rate_limited(ip_address: str) -> bool:
    """
    Checks if client IP address has exceeded upload rate limits.
    """
    now = time.time()
    timestamps = rate_limit_tracker[ip_address]
    # Keep only timestamps within window
    rate_limit_tracker[ip_address] = [ts for ts in timestamps if now - ts < UPLOAD_RATE_LIMIT_WINDOW]
    if len(rate_limit_tracker[ip_address]) >= UPLOAD_RATE_LIMIT_MAX:
        return True
    rate_limit_tracker[ip_address].append(now)
    return False


def create_app(test_config=None):
    """
    Application factory for the Resume Analyzer Flask application.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Configuration loading from environment variables
    env_debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key-resume-analyzer"),
        UPLOAD_FOLDER=os.getenv("UPLOAD_FOLDER", os.path.join(app.root_path, "uploads")),
        MAX_CONTENT_LENGTH=int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)),  # 16 MB max limit
        DEBUG=env_debug
    )

    if test_config:
        app.config.update(test_config)

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/health", methods=["GET"])
    def health_check():
        from services.nlp import embedding_service
        nlp_status = "available" if embedding_service.is_available() else "fallback"
        return jsonify({
            "status": "healthy",
            "nlp": nlp_status
        }), 200

    @app.route("/upload", methods=["POST"])
    def upload_file():
        req_id = uuid.uuid4().hex[:8]
        # Rate limiting check
        client_ip = request.remote_addr or "127.0.0.1"
        if not app.config.get("TESTING") and is_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded request_id={req_id} IP: {client_ip}")
            msg = "Too many upload requests. Please wait a minute before trying again."
            if request.wants_json:
                return jsonify({"success": False, "message": msg}), 429
            flash(msg, "warning")
            return redirect(url_for("index"))

        # Check if post request contains resume file part
        if "resume" not in request.files:
            msg = "No file part in the request."
            if request.wants_json:
                return jsonify({"success": False, "message": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("index"))

        file = request.files["resume"]
        job_description = request.form.get("job_description", "").strip()

        # Job Description size validation
        if len(job_description) > MAX_JD_LENGTH:
            msg = f"Job description exceeds maximum allowed size ({MAX_JD_LENGTH} characters)."
            logger.warning(f"Job description too long request_id={req_id}: {len(job_description)} chars.")
            if request.wants_json:
                return jsonify({"success": False, "message": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("index"))

        success, message, saved_filename = process_upload(file, app.config["UPLOAD_FOLDER"])

        if not success:
            logger.info(f"Upload validation failed request_id={req_id}: {message}")
            if request.wants_json:
                return jsonify({"success": False, "message": message}), 400
            flash(message, "danger")
            return redirect(url_for("index"))

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], saved_filename)
        
        # Temporary file lifecycle cleanup in try ... finally block
        try:
            logger.info(f"Processing upload document request_id={req_id}: {saved_filename}")
            t0 = time.time()
            result = parse_resume(filepath, job_description=job_description)
            duration_ms = int((time.time() - t0) * 1000)
            from services.nlp import embedding_service
            nlp_mode = "embedding" if embedding_service.is_available() else "fallback"
            logger.info(f"analysis_completed request_id={req_id} duration_ms={duration_ms} nlp_mode={nlp_mode} status=success")
        except Exception as e:
            logger.error(f"Unexpected parsing error for {saved_filename}: {str(e)}", exc_info=True)
            result = {
                "filename": file.filename,
                "file_type": "unknown",
                "page_count": None,
                "raw_text": "",
                "cleaned_text": "",
                "has_text": False,
                "sections": {},
                "skills": [],
                "analysis": {"score": 0, "max_score": 100, "categories": {}, "strengths": [], "warnings": [], "recommendations": []},
                "job_match": {"has_job_description": False},
                "evidence_analysis": {"evidence_strength_score": 0, "skill_evidence_list": [], "job_evidence_matrix": [], "evidence_gaps": [], "keyword_coverage": {"matched": 0, "total": 0, "percentage": 0}, "has_job_description": False},
                "recommendation_plan": {"all_recommendations": [], "resume_improvements": [], "job_improvements": [], "has_job_recommendations": False, "counts": {"high": 0, "medium": 0, "low": 0, "total": 0}},
                "error": "Failed to process document content."
            }
        finally:
            # Delete temporary uploaded file from disk to ensure privacy & cleanliness
            if not app.config.get("PRESERVE_UPLOADS") and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    logger.info(f"Cleaned up temporary upload file: {saved_filename}")
                except Exception as cleanup_err:
                    logger.warning(f"Failed to remove temp file {saved_filename}: {cleanup_err}")

        if request.wants_json:
            status_code = 200 if not result.get("error") else 400
            return jsonify({
                "success": not bool(result.get("error")),
                "message": message,
                "result": result
            }), status_code

        return render_template("result.html", result=result)

    # Security HTTP Headers middleware
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "frame-ancestors 'self';"
        )
        return response

    # Global HTTP Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        msg = "Bad Request. Please check your submission."
        if request.wants_json:
            return jsonify({"success": False, "message": msg}), 400
        return render_template("error.html", status_code=400, error_title="Invalid Request", message=msg), 400

    @app.errorhandler(404)
    def page_not_found(error):
        msg = "The requested page or resource could not be found."
        if request.wants_json:
            return jsonify({"success": False, "message": msg}), 404
        return render_template("error.html", status_code=404, error_title="Page Not Found", message=msg), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        msg = "File exceeds the maximum allowed size limit (16MB)."
        if request.wants_json:
            return jsonify({"success": False, "message": msg}), 413
        return render_template("error.html", status_code=413, error_title="File Too Large", message=msg), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        msg = "Too many requests. Please wait a minute before trying again."
        if request.wants_json:
            return jsonify({"success": False, "message": msg}), 429
        return render_template("error.html", status_code=429, error_title="Rate Limit Exceeded", message=msg), 429

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}", exc_info=True)
        msg = "An internal server error occurred. Please try again later."
        if request.wants_json:
            return jsonify({"success": False, "message": msg}), 500
        return render_template("error.html", status_code=500, error_title="Server Error", message=msg), 500

    # Helper property for JSON check
    @app.before_request
    def set_request_helpers():
        request.wants_json = (
            request.is_json
            or request.headers.get("Accept") == "application/json"
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        )

    return app


# Main entry point when running directly
app = create_app()

if __name__ == "__main__":
    app.run()
