"""Pydantic models for API request/response validation."""

from typing import Optional

from pydantic import BaseModel, Field


class PerformanceMetrics(BaseModel):
    """Employee performance metrics."""

    commits: int = Field(default=0, ge=0, description="Number of code commits")
    pr_reviews: int = Field(default=0, ge=0, description="Number of PR reviews conducted")
    tasks_completed: int = Field(default=0, ge=0, description="Number of tasks completed")
    bugs_fixed: int = Field(default=0, ge=0, description="Number of bugs fixed")
    features_delivered: int = Field(default=0, ge=0, description="Number of features shipped")
    incidents_resolved: int = Field(default=0, ge=0, description="On-call incidents handled")
    documentation_pages: int = Field(default=0, ge=0, description="Documentation pages written")


class ProjectDetail(BaseModel):
    """Detailed project information."""

    name: str = Field(..., description="Project name")
    role: str = Field(..., description="Role in project: lead, contributor, reviewer")
    impact: str = Field(..., description="Business impact: e.g., 'Reduced latency by 40%'")
    technologies: list[str] = Field(default=[], description="Technologies used")


class PreviousGoal(BaseModel):
    """Goal from previous review period."""

    goal: str = Field(..., description="The goal that was set")
    status: str = Field(..., description="achieved, partially_achieved, not_achieved, in_progress")
    notes: str = Field(default="", description="Context on the outcome")


class EmployeeCreate(BaseModel):
    """Request body for creating a new employee."""

    # Basic info
    name: str = Field(..., min_length=1, max_length=100, description="Full name")
    role: str = Field(..., min_length=1, max_length=100, description="Job title")
    department: str = Field(..., min_length=1, max_length=100, description="Department")
    level: str = Field(default="", description="Level: junior, mid, senior, staff, principal")
    years_at_company: float = Field(default=0, ge=0, description="Tenure in years")
    review_period: str = Field(default="Q4 2025", description="Review period: e.g., 'Q4 2025'")

    # Detailed projects (replaces simple list)
    projects: list[ProjectDetail] = Field(default=[], description="Detailed project contributions")

    # Skills split into categories
    technical_skills: list[str] = Field(default=[], description="Technical skills")
    soft_skills: list[str] = Field(default=[], description="Soft skills")

    # Metrics
    metrics: PerformanceMetrics = Field(default_factory=PerformanceMetrics)

    # Qualitative feedback
    peer_feedback: list[str] = Field(default=[], description="Peer feedback quotes")
    manager_notes: str = Field(default="", description="Manager observations")

    # Goal tracking
    previous_goals: list[PreviousGoal] = Field(default=[], description="Goals from last period")

    # Growth & development
    training_completed: list[str] = Field(default=[], description="Courses, certs, training")
    mentoring: str = Field(default="", description="Mentoring given/received")

    # Collaboration
    teams_collaborated: list[str] = Field(default=[], description="Cross-functional teams")
    key_contributions: list[str] = Field(default=[], description="Specific contributions beyond projects")

    # Areas identified
    strengths: list[str] = Field(default=[], description="Known strengths")
    growth_areas: list[str] = Field(default=[], description="Areas to improve")

    model_config = {
        "json_schema_extra": {
            "examples": [
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
                            "impact": "Enabled $2M additional monthly revenue, reduced checkout time by 30%",
                            "technologies": ["Python", "FastAPI", "Stripe API", "PostgreSQL"]
                        },
                        {
                            "name": "API Performance Optimization",
                            "role": "contributor",
                            "impact": "Reduced p99 latency from 800ms to 200ms",
                            "technologies": ["Redis", "asyncio", "profiling tools"]
                        },
                        {
                            "name": "Mobile App Backend",
                            "role": "contributor",
                            "impact": "Supported 50K daily active users",
                            "technologies": ["GraphQL", "Docker", "Kubernetes"]
                        }
                    ],
                    "technical_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "AWS"],
                    "soft_skills": ["Team Leadership", "Mentoring", "Technical Writing", "Cross-team Communication"],
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
                        "Great collaborator, always willing to help debug issues - Sarah K.",
                        "His code reviews taught me a lot about writing clean Python - Mike L.",
                        "Calm under pressure during the payment outage - DevOps Team"
                    ],
                    "manager_notes": "John exceeded expectations this quarter. He took ownership of the payment project when it was at risk and delivered on time. His mentorship of junior developers has improved team velocity.",
                    "previous_goals": [
                        {
                            "goal": "Lead a major project end-to-end",
                            "status": "achieved",
                            "notes": "Led payment gateway integration successfully"
                        },
                        {
                            "goal": "Obtain AWS Solutions Architect certification",
                            "status": "in_progress",
                            "notes": "Exam scheduled for January"
                        },
                        {
                            "goal": "Reduce on-call incidents by 20%",
                            "status": "achieved",
                            "notes": "Incidents down 35% through proactive monitoring"
                        }
                    ],
                    "training_completed": [
                        "Advanced Kubernetes Workshop",
                        "Leadership Fundamentals Course"
                    ],
                    "mentoring": "Mentored 2 junior developers (Amy, Carlos) on Python best practices and code review skills",
                    "teams_collaborated": ["DevOps", "Product", "Mobile Team", "Security"],
                    "key_contributions": [
                        "Created team's first runbook for incident response",
                        "Introduced automated testing standards that reduced bugs by 40%",
                        "Led weekly architecture review sessions"
                    ],
                    "strengths": [
                        "Deep technical expertise in Python ecosystem",
                        "Strong ownership mentality",
                        "Effective cross-team communication"
                    ],
                    "growth_areas": [
                        "Public speaking and presenting to larger groups",
                        "Delegating tasks instead of taking everything on"
                    ]
                }
            ]
        }
    }


class EmployeeUpdate(BaseModel):
    """Request body for updating an employee (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    level: Optional[str] = None
    years_at_company: Optional[float] = None
    review_period: Optional[str] = None
    projects: Optional[list[ProjectDetail]] = None
    technical_skills: Optional[list[str]] = None
    soft_skills: Optional[list[str]] = None
    metrics: Optional[PerformanceMetrics] = None
    peer_feedback: Optional[list[str]] = None
    manager_notes: Optional[str] = None
    previous_goals: Optional[list[PreviousGoal]] = None
    training_completed: Optional[list[str]] = None
    mentoring: Optional[str] = None
    teams_collaborated: Optional[list[str]] = None
    key_contributions: Optional[list[str]] = None
    strengths: Optional[list[str]] = None
    growth_areas: Optional[list[str]] = None


class EmployeeResponse(BaseModel):
    """Response model for employee data."""

    id: str = Field(..., description="MongoDB document ID")
    name: str
    role: str
    department: str
    level: str = ""
    years_at_company: float = 0
    review_period: str = ""
    projects: list[ProjectDetail] = []
    technical_skills: list[str] = []
    soft_skills: list[str] = []
    metrics: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    peer_feedback: list[str] = []
    manager_notes: str = ""
    previous_goals: list[PreviousGoal] = []
    training_completed: list[str] = []
    mentoring: str = ""
    teams_collaborated: list[str] = []
    key_contributions: list[str] = []
    strengths: list[str] = []
    growth_areas: list[str] = []


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    id: Optional[str] = None


class OnboardingRequest(BaseModel):
    """Request body for onboarding request."""

    employee_name: str = Field(..., min_length=1, description="New hire name")
    role: str = Field(..., description="Job title")
    department: str = Field(..., description="Department")
    start_date: str = Field(..., description="Start date: YYYY-MM-DD")
    manager_name: str = Field(..., description="Direct manager name")
    buddy_name: str = Field(default="", description="Assigned buddy/mentor")
    equipment: list[str] = Field(default=[], description="Equipment needed")
    systems_access: list[str] = Field(default=[], description="Systems needing access")
    training_required: list[str] = Field(default=[], description="Required training")
    team_members: list[str] = Field(default=[], description="Team members to meet")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "employee_name": "Jane Smith",
                    "role": "Backend Engineer",
                    "department": "Engineering",
                    "start_date": "2026-01-15",
                    "manager_name": "John Doe",
                    "buddy_name": "Mike Johnson",
                    "equipment": ["MacBook Pro 16", "Monitor", "Keyboard", "Mouse"],
                    "systems_access": ["GitHub", "Jira", "Slack", "AWS Console", "VPN"],
                    "training_required": ["Security Awareness", "Code Standards", "CI/CD Pipeline"],
                    "team_members": ["Sarah K.", "Mike L.", "Carlos R.", "Amy T."]
                }
            ]
        }
    }
