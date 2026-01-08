# HR Document Generator

A local LLM-powered tool for generating performance reviews and onboarding plans using GPU acceleration.

## Features

- Generate performance reviews with 3 template styles (formal, casual, technical)
- Generate onboarding plans for new hires
- PDF export with professional styling
- GPU-accelerated inference (NVIDIA CUDA)
- Response caching for faster repeat requests
- RESTful API with FastAPI
- MongoDB for employee data storage

## Requirements

- Python 3.10+
- MongoDB
- Llama 3.2 3B model (GGUF format)
- NVIDIA GPU with CUDA 12+ (recommended) or CPU fallback

## Installation

```bash
cd performance-review-generator
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### GPU Setup (Recommended)

For GPU acceleration, install llama-cpp-python with CUDA support:

```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

Requires CUDA 12.1+ toolkit installed on your system.

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Database
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=hr_database
EMPLOYEES_COLLECTION=employees

# Model settings
MODEL_PATH=/path/to/llama-3.2-3b-instruct-q4_k_m.gguf
MODEL_THREADS=2            # CPU threads (lower when using GPU)
MODEL_CTX=3072             # Context size
MODEL_BATCH=512            # Batch size for prompt processing
MODEL_GPU_LAYERS=-1        # -1 = all layers on GPU, 0 = CPU only

# Performance
CACHE_ENABLED=true         # Cache responses for identical requests

# Output
OUTPUT_DIR=./output
```

### GPU vs CPU Configuration

| Setting | GPU (Recommended) | CPU Only |
|---------|-------------------|----------|
| `MODEL_GPU_LAYERS` | `-1` (all layers) | `0` |
| `MODEL_THREADS` | `2` | `4-6` |
| Expected Speed | ~6s per review | ~12s per review |

---

## Postman Collection

Import the Postman collection for easy API testing:

```
postman/HR_Document_Generator.postman_collection.json
```

The collection includes all endpoints with sample request bodies.

---

## Quick Start

### 1. Start the API Server

```bash
python api/server.py
```

### 2. Create an Employee

```bash
curl -X POST "http://localhost:8000/api/v2/employees/" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "role": "Software Engineer", "department": "Engineering"}'
```

### 3. Generate a Review

```bash
curl -X POST "http://localhost:8000/api/v2/generate/review/John%20Doe?template=formal&export_pdf=true"
```

---

## CLI Usage

### List Employees

```bash
python main.py --list
```

### Generate Single Performance Review

```bash
python main.py --employee "John Doe"
```

### Generate All Performance Reviews

```bash
python main.py --all
```

### Generate Onboarding Plan

```bash
python main.py --onboarding onboarding_example.json
```

---

## API Reference

Base URL: `http://localhost:8000/api/v2`

Interactive docs: `http://localhost:8000/api/v2/docs`

---

### Health Check

```
GET /
```

Response:
```json
{
  "status": "healthy",
  "service": "hr-document-generator",
  "version": "2.0.0",
  "api": "/api/v2",
  "llm_loaded": true
}
```

---

## Employee Endpoints

### Create Employee

```
POST /api/v2/employees/
Content-Type: application/json
```

Request:
```json
{
  "name": "John Doe",
  "role": "Senior Software Engineer",
  "department": "Engineering",
  "level": "senior",
  "years_at_company": 3.5,
  "review_period": "Q4 2025",
  "projects": [
    {
      "name": "Payment Gateway Integration",
      "role": "lead",
      "impact": "Enabled $2M additional monthly revenue",
      "technologies": ["Python", "FastAPI", "PostgreSQL"]
    }
  ],
  "technical_skills": ["Python", "FastAPI", "Docker"],
  "soft_skills": ["Team Leadership", "Mentoring"],
  "metrics": {
    "commits": 245,
    "pr_reviews": 89,
    "tasks_completed": 67,
    "bugs_fixed": 23,
    "features_delivered": 8,
    "incidents_resolved": 5,
    "documentation_pages": 12
  },
  "peer_feedback": [
    "Great collaborator - Sarah K.",
    "Excellent code reviews - Mike L."
  ],
  "manager_notes": "Exceeded expectations this quarter.",
  "previous_goals": [
    {
      "goal": "Lead a major project",
      "status": "achieved",
      "notes": "Led payment integration successfully"
    }
  ],
  "training_completed": ["Kubernetes Workshop"],
  "mentoring": "Mentored 2 junior developers",
  "teams_collaborated": ["DevOps", "Product"],
  "key_contributions": ["Created incident response runbook"],
  "strengths": ["Python expertise", "Ownership mentality"],
  "growth_areas": ["Public speaking"]
}
```

Response `201 Created`:
```json
{
  "message": "Employee 'John Doe' created successfully",
  "id": "678d4f..."
}
```

---

### List All Employees

```
GET /api/v2/employees/
```

Response `200 OK`:
```json
[
  {
    "id": "678d4f...",
    "name": "John Doe",
    "role": "Senior Software Engineer",
    "department": "Engineering"
  }
]
```

---

### Get Employee

```
GET /api/v2/employees/{name}
```

Example: `GET /api/v2/employees/John%20Doe`

---

### Update Employee

```
PUT /api/v2/employees/{name}
Content-Type: application/json
```

Request (partial update):
```json
{
  "role": "Staff Engineer",
  "level": "staff"
}
```

---

### Delete Employee

```
DELETE /api/v2/employees/{name}
```

---

## Generation Endpoints

### List Available Templates

```
GET /api/v2/generate/templates
```

Response:
```json
{
  "templates": [
    {
      "name": "formal",
      "description": "Traditional corporate HR style - professional, objective, third-person",
      "best_for": "Official HR records, large corporations, formal review processes"
    },
    {
      "name": "casual",
      "description": "Modern friendly style - warm, encouraging, first-person",
      "best_for": "Startups, small teams, regular check-ins"
    },
    {
      "name": "technical",
      "description": "Engineering-focused style - metrics-heavy, precise, technical",
      "best_for": "Engineering teams, technical roles, performance benchmarking"
    }
  ]
}
```

---

### Generate Performance Review

```
POST /api/v2/generate/review/{employee_name}?template={style}&export_pdf={bool}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `employee_name` | path | required | Employee name |
| `template` | query | `formal` | Style: `formal`, `casual`, `technical` |
| `export_pdf` | query | `false` | Also generate PDF version |

Example:
```bash
curl -X POST "http://localhost:8000/api/v2/generate/review/John%20Doe?template=casual&export_pdf=true"
```

Response `200 OK`:
```json
{
  "success": true,
  "employee_name": "John Doe",
  "file_path": "./output/review_john_doe_casual_20260108.md",
  "pdf_path": "./output/review_john_doe_casual_20260108.pdf",
  "template": "casual",
  "message": "Performance review (casual) generated successfully in 6.12s",
  "generated_at": "2026-01-08T10:30:00"
}
```

---

### Generate Onboarding Plan

```
POST /api/v2/generate/onboarding
Content-Type: application/json
```

Request:
```json
{
  "employee_name": "Jane Smith",
  "role": "Backend Engineer",
  "department": "Engineering",
  "start_date": "2026-02-01",
  "manager_name": "John Doe",
  "buddy_name": "Mike Johnson",
  "team_size": 8,
  "remote": false,
  "equipment_needed": ["MacBook Pro 16", "Monitor"],
  "access_needed": ["GitHub", "Jira", "Slack", "AWS"]
}
```

Response `200 OK`:
```json
{
  "success": true,
  "employee_name": "Jane Smith",
  "file_path": "./output/onboarding_jane_smith_20260108.md",
  "message": "Onboarding plan generated successfully in 5.89s",
  "generated_at": "2026-01-08T10:35:00"
}
```

---

### Convert Markdown to PDF

```
POST /api/v2/generate/convert-to-pdf
Content-Type: application/json
```

Request:
```json
{
  "markdown_path": "./output/review_john_doe_formal_20260108.md",
  "template": "formal"
}
```

Response `200 OK`:
```json
{
  "success": true,
  "pdf_path": "./output/review_john_doe_formal_20260108.pdf",
  "message": "PDF created successfully with formal template"
}
```

---

### Download Generated File

```
GET /api/v2/generate/download/{filename}
```

Example:
```bash
curl -O "http://localhost:8000/api/v2/generate/download/review_john_doe_formal_20260108.pdf"
```

Returns the file for download (markdown or PDF).

---

## Review Templates

| Template | Tone | Use Case |
|----------|------|----------|
| **formal** | Corporate, third-person, objective | Official HR records, large companies |
| **casual** | Friendly, first-person, encouraging | Startups, regular check-ins |
| **technical** | Metrics-focused, precise, detailed | Engineering teams, technical roles |

---

## Project Structure

```
performance-review-generator/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── config.py
├── logging_config.py
├── main.py
├── database/
│   ├── __init__.py
│   └── mongo.py
├── llm/
│   ├── __init__.py
│   └── local_model.py
├── generator/
│   ├── __init__.py
│   ├── prompts.py
│   ├── templates.py          # Review templates (formal, casual, technical)
│   ├── pdf_export.py         # PDF generation utility
│   ├── review.py
│   ├── onboarding_prompts.py
│   └── onboarding.py
├── api/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── generate_routes.py
│   └── server.py
├── postman/
│   └── HR_Document_Generator.postman_collection.json
└── output/
    ├── review_*.md
    └── review_*.pdf
```

---

## Output Files

| Type | Filename Pattern |
|------|------------------|
| Performance Review (MD) | `review_{name}_{template}_{date}.md` |
| Performance Review (PDF) | `review_{name}_{template}_{date}.pdf` |
| Onboarding Plan | `onboarding_{name}_{date}.md` |

All generated documents are saved to the `output/` directory.

---

## Performance

With GPU acceleration (NVIDIA Quadro M4000 / similar):

| Operation | Time |
|-----------|------|
| Model loading | ~3-5s |
| Review generation | ~6s |
| PDF export | ~1s |

Cached responses return instantly.
