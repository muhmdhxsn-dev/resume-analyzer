# Resume Analyzer & Job Match Engine

A production-ready, lightweight, and maintainable Flask web application for uploading resumes, extracting text, detecting canonical sections, extracting multi-domain skills, evaluating a 100-point Adaptive Resume Quality Score, performing Semantic Job Matching, generating a Prioritized Actionable Improvement Plan, analyzing Skill Evidence Strength & Location Intelligence, enforcing production security safeguards, and delivering **AI/NLP Candidate Intelligence**.

---

## 🚀 Deployment Modes & Architecture

The application supports dual deployment architectures depending on hosting requirements:

### 1. Vercel Serverless Deployment (`requirements.txt`)
- **Runtime**: Vercel Serverless Functions (`@vercel/python` builder)
- **Dependencies**: Lightweight (`Flask`, `PyMuPDF`, `python-docx`, `python-dotenv`, `gunicorn`) — total bundle footprint **< 25 MB** (well below Vercel's 500 MB limit).
- **NLP Engine**: Deterministic Token Jaccard Similarity Fallback. Automatically activates when `VERCEL=1` is set or when heavy ML libraries are absent.
- **Health Check (`GET /health`)**: Reports `{"status": "healthy", "nlp": "fallback"}`.
- **Advantages**: $0/month serverless hosting, fast deployment, 0 heavy PyTorch binary dependencies, zero cold-start model downloads.

### 2. Full Local / Containerized Deployment (`requirements-full.txt`)
- **Runtime**: Gunicorn WSGI (`gunicorn --workers 1 --threads 2 --timeout 120 wsgi:application`) or local development server.
- **Dependencies**: Full ML stack (`sentence-transformers==6.0.0`, `scikit-learn==1.9.0`, PyTorch CPU).
- **NLP Engine**: SentenceTransformers (`all-MiniLM-L6-v2`) + Thread-Safe LRU Vector Embedding Cache (`_EMBEDDING_CACHE`).
- **Health Check (`GET /health`)**: Reports `{"status": "healthy", "nlp": "available"}`.
- **Advantages**: High-precision vector cosine embedding similarity for nuanced semantic matching.

---

## 📁 Project Structure

```text
resume-analyzer/
├── app.py                  # Flask application factory, security headers, rate limiting, & error handlers
├── wsgi.py                 # Production WSGI server entrypoint (exports both app and application)
├── Procfile                # WSGI startup configuration for production hosting (Gunicorn)
├── api/
│   └── index.py            # Vercel serverless function entrypoint
├── vercel.json             # Vercel serverless routing configuration
├── data/
│   ├── skills.json         # Combined skill catalog for backward compatibility
│   ├── skills/             # Multi-domain skill catalogs (tech, finance, marketing, healthcare, etc.)
│   └── occupations/
│       └── domains.json    # Occupation taxonomy definitions & anchor phrases
├── services/
│   ├── upload_service.py   # Magic header validation, UUID filename sanitization, & saving
│   ├── resume_parser.py    # Document parsing for PDF (PyMuPDF) and DOCX (python-docx) with page limits
│   ├── text_processor.py   # Conservative text cleaning & whitespace normalization
│   ├── section_detector.py # Automatic resume structure detection line-by-line
│   ├── skill_extractor.py  # Multi-domain skill extraction with boundary matching
│   ├── candidate_profile.py # Domain-agnostic candidate profile normalization
│   ├── resume_analyzer.py  # Adaptive scoring, domain weights, achievement detection, & feedback
│   ├── job_matcher.py      # Hybrid exact + semantic job matching engine
│   ├── recommendation_service.py # Actionable 3-part recommendation plan generator
│   ├── evidence_analyzer.py # Skill location analysis, alias normalization, & evidence matrix
│   └── nlp/                # AI/NLP Intelligence Module
│       ├── embedding_service.py # Vector embedding service with LRU cache & Vercel fallback
│       ├── domain_detector.py   # Domain & role classifier
│       └── semantic_skill_extractor.py # Categorized skill extraction & implicit phrase matching
├── templates/
│   ├── index.html          # Modern SaaS homepage with hero CTA & drag-and-drop upload zone
│   ├── result.html         # Score dashboards, Candidate Intelligence, Job Evidence Matrix, & Skills
│   └── error.html          # Custom error page for 400, 404, 413, 429, & 500 status codes
├── static/
│   ├── css/style.css       # SaaS design system, progress ring gauges, & responsive rules
│   └── js/app.js           # Vanilla JS handling drag-and-drop & loading animations
├── uploads/
│   └── .gitkeep            # Directory for temporary upload files
├── tests/                  # Automated test suite (115 passing tests)
├── requirements.txt        # Lightweight dependencies for Vercel deployment
├── requirements-full.txt   # Full dependencies including Sentence Transformers & PyTorch
├── requirements-dev.txt    # Development & testing dependencies (includes pytest)
├── .env.example            # Environment configuration template
└── README.md               # Documentation
```

---

## ⚙️ Environment Variables

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `FLASK_ENV` | `production` | Flask runtime mode |
| `SECRET_KEY` | `dev-secret-...` | Flask session cookie signing secret |
| `MAX_CONTENT_LENGTH` | `16777216` | Max upload size in bytes (16MB) |
| `MAX_JD_LENGTH` | `10000` | Max job description character limit |
| `MAX_PDF_PAGES` | `50` | Max PDF document page limit |
| `NLP_MODEL_NAME` | `all-MiniLM-L6-v2` | SentenceTransformer model name *(full NLP mode only)* |
| `EMBEDDING_CACHE_SIZE` | `2000` | Vector LRU cache limit *(full NLP mode only)* |
| `VERCEL` | *(Auto-set)* | Set automatically on Vercel to activate lightweight fallback mode |

---

## 🔒 Security Safeguards

- **Binary Magic Header Validation**: Validates `%PDF-` and `PK\x03\x04` bytes.
- **Path Traversal Protection**: Enforces `secure_filename()` + UUID prefixes.
- **XSS Autoescaping**: Jinja autoescapes raw text inputs.
- **HTTP Security Headers**: Enforces CSP, `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`.
- **Ephemeral Cleanup**: Temporary upload files in `/tmp` or `uploads/` are deleted in `finally` blocks.

---

## 🧪 Testing

Run test suite:
```bash
pytest -v
```

**Results**: 115 passed in ~100 seconds (100% pass rate).
