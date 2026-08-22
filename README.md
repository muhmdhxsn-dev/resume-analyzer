# Resume Analyzer & Job Match Engine

A production-ready, lightweight, and maintainable Flask web application for uploading resumes, extracting text, detecting canonical sections, extracting multi-domain skills, evaluating a 100-point Adaptive Resume Quality Score, performing Semantic Job Matching, generating a Prioritized Actionable Improvement Plan, analyzing Skill Evidence Strength & Location Intelligence, enforcing production security safeguards, and delivering **AI/NLP Candidate Intelligence**.

---

## 📁 Project Structure

```text
resume-analyzer/
├── app.py                  # Flask application factory, security headers, rate limiting, & error handlers
├── wsgi.py                 # Production WSGI server entrypoint (exports both app and application)
├── Procfile                # WSGI startup configuration for production hosting (Gunicorn)
├── data/
│   ├── skills.json         # Combined skill catalog for backward compatibility
│   ├── skills/             # Multi-domain skill catalogs
│   │   ├── tech.json
│   │   ├── finance.json
│   │   ├── marketing.json
│   │   ├── healthcare.json
│   │   ├── education.json
│   │   ├── soft_skills.json
│   │   └── tools.json
│   └── occupations/
│       └── domains.json    # Occupation taxonomy definitions & anchor phrases
├── services/
│   ├── __init__.py
│   ├── upload_service.py   # Magic header validation, UUID filename sanitization, & saving
│   ├── resume_parser.py    # Document parsing for PDF (PyMuPDF) and DOCX (python-docx) with page limit safeguards
│   ├── text_processor.py   # Conservative text cleaning & whitespace normalization
│   ├── section_detector.py # Automatic resume structure detection line-by-line
│   ├── skill_extractor.py  # Multi-domain skill extraction with boundary matching
│   ├── candidate_profile.py # Domain-agnostic candidate profile normalization
│   ├── resume_analyzer.py  # Adaptive scoring, domain weights, achievement detection, & explainable feedback
│   ├── job_matcher.py      # Hybrid exact + semantic job matching engine
│   ├── recommendation_service.py # Prioritized 3-part actionable recommendation plan generator
│   ├── evidence_analyzer.py # Skill location analysis, alias normalization, evidence matrix, & gaps
│   └── nlp/                # AI/NLP Intelligence Module
│       ├── __init__.py
│       ├── embedding_service.py # Sentence-transformers vector embedding service with thread-safe LRU caching
│       ├── domain_detector.py   # Domain & role classifier
│       └── semantic_skill_extractor.py # Categorized skill extraction & implicit phrase matching
├── templates/
│   ├── index.html          # Modern SaaS homepage with hero CTA & drag-and-drop upload zone
│   ├── result.html         # Score dashboards, Candidate Intelligence, Job Evidence Matrix, & Skills
│   └── error.html          # Custom error page for 400, 404, 413, 429, & 500 status codes
├── static/
│   ├── css/
│   │   └── style.css       # SaaS design system, progress ring gauges, evidence tables, & responsive rules
│   └── js/
│       └── app.js          # Vanilla JS handling drag-and-drop, CTA scrolling, & step-by-step loading
├── uploads/
│   └── .gitkeep            # Directory for temporary upload files
├── tests/
│   ├── __init__.py
│   ├── test_app.py         # Flask route integration & upload tests
│   ├── test_parser.py      # Unit tests for PDF, DOCX, text processor, & error cases
│   ├── test_section_detector.py # Unit tests for section heading matching & section separation
│   ├── test_skill_extractor.py  # Unit tests for skill extraction & multi-domain catalogs
│   ├── test_resume_analyzer.py # Unit tests for feature extraction, quality score, & feedback
│   ├── test_adaptive_scoring.py # Unit tests for domain scoring profiles & non-penalty optional sections
│   ├── test_job_matcher.py      # Unit tests for JD skill extraction & match score
│   ├── test_semantic_job_matcher.py # Unit tests for semantic job matching & cross-domain protection
│   ├── test_recommendation_service.py # Unit tests for 3-part recommendation plan & priorities
│   ├── test_evidence_analyzer.py # Unit tests for skill evidence strength & alias normalization
│   ├── test_production.py  # Unit tests for magic headers, temp file cleanup, security, & path traversal safety
│   ├── test_nlp_intelligence.py # Unit tests for domain detection, semantic similarity, & NLP fallback
│   └── test_phase14_evaluation.py # Multi-domain synthetic evaluation suite (10 domain profiles)
├── requirements.txt        # Dependencies (Flask, python-dotenv, pytest, PyMuPDF, python-docx, gunicorn, sentence-transformers, scikit-learn)
├── .env.example            # Environment configuration template
├── .env                    # Local environment variables file (git-ignored)
├── .gitignore              # Git ignore rules
└── README.md               # Documentation
```

---

## 🏗 Architecture Pipeline

```text
Resume Upload
  ↓
File Validation & Security (Magic Headers, Size Limit, Sanitization)
  ↓
Document Parsing (PDF PyMuPDF / DOCX python-docx)
  ↓
Section Detection & Structure Extraction
  ↓
CandidateProfile Normalization (Domain & Role Inferencing)
  ↓
Adaptive Resume Scoring & Achievement Detection
  ↓
Semantic Job Matching (Hybrid Exact + Vector Similarity)
  ↓
Job Evidence Matrix & Skill Gap Identification
  ↓
Non-Fabricating Recommendations
  ↓
Modern SaaS UI Dashboard Rendering
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.12+**
- `pip` package manager

### 2. Local Setup

```powershell
# 1. Clone the repository
git clone <repository-url>
cd resume-analyzer

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure local environment variables
cp .env.example .env
```

### 3. Running the Application

```bash
python wsgi.py
```

Access the application in your browser at [http://127.0.0.1:5000](http://127.0.0.1:5000).

---

## 🤖 AI/NLP Candidate Intelligence

The application features a CPU-optimized, pretrained NLP vector embedding model (`sentence-transformers/all-MiniLM-L6-v2` ~90MB) with thread-safe in-memory caching:

- **Supported Domain Profiles**: Explicit scoring profiles exist for `Software Engineering & IT`, `Finance & Accounting`, `Marketing & Sales`, `Healthcare & Medicine`, `Education & Teaching`, and `Human Resources & Administration`. Other domains gracefully use the neutral `Default` scoring profile.
- **Adaptive Domain Scoring**: Re-scales category score weights dynamically (e.g. Accountants, Teachers, Nurses, and Sales Reps receive zero penalty for lacking a software Projects section).
- **Categorized Skill Extraction**: Automatically separates extracted skills into `Technical Skills`, `Tools & Software`, `Soft Skills`, and `Domain Competencies`.
- **Hybrid Job Matcher**: Blends exact skill matching (60%) and vector embedding semantic similarity (40%) with cross-domain negative match protection.
- **In-Memory Embedding Caching**: Caches float vector representations for identical text snippets, accelerating warm test runtimes from **114.29s** down to **49.84s** (**2.3x speedup**).
- **Deterministic Fallback**: If model loading or network availability prevents embedding model loading, the system gracefully falls back to Jaccard token overlap similarity without crashing.
- **Non-Fabricating Recommendations**: Recommendations are generated strictly from detected resume evidence and job requirements without intentionally inventing unsupported certifications or experience.

---

## 🔒 Security Safeguards

Security controls were implemented and validated through automated regression tests:
- **Magic Header Validation**: Rejects spoofed binaries.
- **Filename Sanitization**: UUID prefixing prevents path traversal attacks (`../../../resume.pdf`).
- **Resource Limits**: 16MB max upload limit, 10,000 character job description limit, and 50-page PDF limit.
- **HTTP Security Headers**: `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy` headers enabled.
- **Temporary File Lifecycle**: Guaranteed `try...finally` deletion of uploaded temp files.

---

## 🧪 Running Tests

Evaluated across 10 synthetic multi-domain professional profiles with 111 automated tests:

```bash
pytest -v
```

---

## 🌐 Production Deployment

The project is fully prepared for production deployment on WSGI hosting platforms (e.g. Render, Railway, Heroku, AWS Elastic Beanstalk, or Gunicorn behind Nginx).

### Production Server Startup Command:
```bash
gunicorn wsgi:application
```
*(Alternatively `gunicorn wsgi:app`)*

### Recommended Gunicorn Worker Configuration:
Because the embedding model memory is process-local (~90MB RSS per worker process), a conservative worker configuration is recommended:
```bash
gunicorn --workers 2 --threads 2 wsgi:application
```
