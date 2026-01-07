# HR Document Generator

A local LLM-powered tool for generating performance reviews and onboarding plans.

## Requirements

- Python 3.10+
- MongoDB
- Llama 3.2 3B model (GGUF format)

## Installation

```bash
cd performance-review-generator
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and configure:

```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=hr_database
EMPLOYEES_COLLECTION=employees
MODEL_PATH=/path/to/llama-3.2-3b-instruct-q4_k_m.gguf
MODEL_THREADS=6
MODEL_CTX=4096
OUTPUT_DIR=./output
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

Output: `output/review_john_doe_20260107.md`

### Generate All Performance Reviews

```bash
python main.py --all
```

### Generate Onboarding Plan

```bash
python main.py --onboarding onboarding_example.json
```

Output: `output/onboarding_jane_smith_20260107.md`

---

## API Reference

Start the API server:

```bash
uvicorn api.server:app --reload --port 8000
```

API documentation available at `http://localhost:8000/docs`

---

### Health Check

```
GET /
```

Response:
```json
{
  "status": "healthy",
  "service": "performance-review-api"
}
```

---

### Create Employee

```
POST /employees/
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
GET /employees/
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
GET /employees/{name}
```

Example: `GET /employees/John%20Doe`

Response `200 OK`:
```json
{
  "id": "678d4f...",
  "name": "John Doe",
  "role": "Senior Software Engineer",
  "department": "Engineering",
  "level": "senior",
  "years_at_company": 3.5,
  "projects": [...],
  "metrics": {...}
}
```

Response `404 Not Found`:
```json
{
  "detail": "Employee 'John Doe' not found"
}
```

---

### Update Employee

```
PUT /employees/{name}
Content-Type: application/json
```

Request (partial update):
```json
{
  "role": "Staff Engineer",
  "level": "staff"
}
```

Response `200 OK`:
```json
{
  "message": "Employee 'John Doe' updated successfully"
}
```

---

### Delete Employee

```
DELETE /employees/{name}
```

Response `200 OK`:
```json
{
  "message": "Employee 'John Doe' deleted successfully"
}
```

---

## Onboarding JSON Schema

```json
{
  "employee_name": "Jane Smith",
  "role": "Backend Engineer",
  "department": "Engineering",
  "start_date": "2026-01-15",
  "manager_name": "John Doe",
  "buddy_name": "Mike Johnson",
  "equipment": ["MacBook Pro 16", "Monitor", "Keyboard"],
  "systems_access": ["GitHub", "Jira", "Slack", "AWS Console"],
  "training_required": ["Security Awareness", "Code Standards"],
  "team_members": ["Sarah K.", "Mike L.", "Carlos R."]
}
```

---

## Project Structure

```
performance-review-generator/
├── .env
├── .env.example
├── requirements.txt
├── config.py
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
│   ├── review.py
│   ├── onboarding_prompts.py
│   └── onboarding.py
├── api/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── server.py
└── output/
```

---

## Output Files

| Type | Filename Pattern |
|------|------------------|
| Performance Review | `review_{name}_{date}.md` |
| Onboarding Plan | `onboarding_{name}_{date}.md` |

All generated documents are saved to the `output/` directory.
