import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Magic headers byte signatures
PDF_MAGIC = b'%PDF-'
ZIP_DOCX_MAGIC = b'PK\x03\x04'


def allowed_file(filename: str) -> bool:
    """
    Check if a filename has an allowed extension (.pdf or .docx).
    """
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_file_magic(file) -> tuple[bool, str]:
    """
    Inspects initial file bytes to verify magic header content matches expected PDF or DOCX structure.
    Rewinds the stream position after reading.
    """
    try:
        header = file.read(512)
        file.seek(0)  # Rewind stream position

        if not header:
            return False, "File is empty."

        filename = getattr(file, 'filename', '')
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

        if ext == 'pdf':
            if not header.startswith(PDF_MAGIC):
                return False, "Invalid file content. The uploaded file header does not match a valid PDF format."
        elif ext == 'docx':
            if not header.startswith(ZIP_DOCX_MAGIC):
                return False, "Invalid file content. The uploaded file header does not match a valid DOCX format."
        
        return True, ""
    except Exception as e:
        return False, f"Failed to validate file headers: {str(e)}"


def process_upload(file, upload_folder: str):
    """
    Validates extension, inspects magic headers, sanitizes filename,
    generates a safe UUID temporary file path, and saves the file.
    
    Returns:
        tuple: (success: bool, message: str, saved_filename: str | None)
    """
    if file is None or file.filename == '':
        return False, "No file selected for upload. Please select a PDF or DOCX file.", None

    if not allowed_file(file.filename):
        return False, f"Invalid file extension. Only {', '.join(sorted(ALLOWED_EXTENSIONS)).upper()} files are allowed.", None

    # Magic header content inspection
    is_valid_magic, magic_msg = validate_file_magic(file)
    if not is_valid_magic:
        return False, magic_msg, None

    # Secure filename sanitization & UUID prefix to prevent collisions and path traversal
    base_name = secure_filename(file.filename)
    if not base_name:
        base_name = "resume_document"
    
    ext = base_name.rsplit('.', 1)[-1].lower() if '.' in base_name else 'pdf'
    unique_prefix = uuid.uuid4().hex
    saved_filename = f"{unique_prefix}_{base_name}"

    # Ensure upload directory exists
    os.makedirs(upload_folder, exist_ok=True)

    filepath = os.path.join(upload_folder, saved_filename)
    file.save(filepath)

    return True, f"File '{file.filename}' successfully uploaded!", saved_filename
