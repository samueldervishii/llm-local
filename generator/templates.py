"""Review templates with different styles: formal, casual, technical."""

from enum import Enum
from typing import NamedTuple


class ReviewStyle(str, Enum):
    """Available review styles."""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"


class ReviewTemplate(NamedTuple):
    """Template configuration."""
    system_prompt: str
    sections: str
    tone_guide: str


# =============================================================================
# FORMAL TEMPLATE - Traditional corporate HR style
# =============================================================================
FORMAL_SYSTEM_PROMPT = """You are a senior HR professional drafting formal performance reviews.
Generate professional, objective, and balanced content suitable for official HR records.
Use formal language and third-person perspective.
Be SPECIFIC - reference exact numbers, project names, and metrics from the data.
Maintain a professional, respectful tone throughout."""

FORMAL_SECTIONS = """
Generate these sections using the data above. Use formal third-person language:

1. EXECUTIVE SUMMARY (2-3 paragraphs - formal assessment of overall performance)

2. KEY ACCOMPLISHMENTS (4-5 bullets - measurable achievements with business impact)

3. GOAL ATTAINMENT REVIEW (assess each previous goal with formal status)

4. DEVELOPMENT OPPORTUNITIES (2-3 areas for professional growth)

5. OBJECTIVES FOR NEXT REVIEW PERIOD (3-4 SMART goals aligned with business needs)

6. COMPETENCY ASSESSMENT QUESTIONS (3 role-specific evaluation questions)

7. LEADERSHIP POTENTIAL INDICATORS (3 questions assessing growth potential)

Use markdown formatting with ## headers. Maintain formal corporate tone."""

# =============================================================================
# CASUAL TEMPLATE - Modern, friendly startup style
# =============================================================================
CASUAL_SYSTEM_PROMPT = """You are a friendly team lead writing a performance check-in.
Generate warm, encouraging, and genuine feedback that feels personal.
Use first-person perspective and conversational language.
Be SPECIFIC - reference exact numbers, project names, and wins from the data.
Keep the tone supportive and growth-focused, like talking to a valued teammate."""

CASUAL_SECTIONS = """
Generate these sections using the data above. Use friendly, first-person language:

1. THE BIG PICTURE (2-3 paragraphs - genuine reflection on their journey this quarter)

2. WINS WORTH CELEBRATING (4-5 bullets - highlight achievements with enthusiasm)

3. HOW'D THOSE GOALS GO? (friendly check-in on each previous goal)

4. ROOM TO GROW (2-3 growth areas framed as exciting opportunities)

5. WHAT'S NEXT? (3-4 goals framed as exciting challenges ahead)

6. SKILLS DEEP-DIVE (3 questions to explore their technical growth)

7. TEAM DYNAMICS CHECK (3 questions about collaboration and communication)

Use markdown formatting with ## headers. Keep it warm and encouraging!"""

# =============================================================================
# TECHNICAL TEMPLATE - Engineering-focused, metrics-heavy
# =============================================================================
TECHNICAL_SYSTEM_PROMPT = """You are a technical engineering manager writing a performance review.
Generate detailed, metrics-driven, and technically-focused content.
Emphasize code quality, system impact, and technical decision-making.
Be SPECIFIC - reference exact commit counts, latency improvements, and technical achievements.
Use precise technical language appropriate for engineering documentation."""

TECHNICAL_SECTIONS = """
Generate these sections using the data above. Focus on technical metrics and impact:

1. TECHNICAL PERFORMANCE OVERVIEW (2-3 paragraphs - emphasize system impact and code quality)

2. ENGINEERING ACHIEVEMENTS (4-5 bullets - include specific metrics: latency, throughput, uptime)

3. GOAL COMPLETION METRICS (assess each goal with quantitative outcomes)

4. TECHNICAL DEBT & GROWTH VECTORS (2-3 specific technical areas for improvement)

5. ENGINEERING OBJECTIVES Q+1 (3-4 technically-scoped, measurable goals)

6. TECHNICAL ASSESSMENT (3 architecture/design questions based on their stack)

7. ENGINEERING LEADERSHIP (3 questions on mentorship, code review, and technical decisions)

Use markdown formatting with ## headers. Include specific numbers and technical details."""


# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================
TEMPLATES: dict[ReviewStyle, ReviewTemplate] = {
    ReviewStyle.FORMAL: ReviewTemplate(
        system_prompt=FORMAL_SYSTEM_PROMPT,
        sections=FORMAL_SECTIONS,
        tone_guide="formal third-person corporate"
    ),
    ReviewStyle.CASUAL: ReviewTemplate(
        system_prompt=CASUAL_SYSTEM_PROMPT,
        sections=CASUAL_SECTIONS,
        tone_guide="friendly first-person conversational"
    ),
    ReviewStyle.TECHNICAL: ReviewTemplate(
        system_prompt=TECHNICAL_SYSTEM_PROMPT,
        sections=TECHNICAL_SECTIONS,
        tone_guide="precise technical metrics-focused"
    ),
}


def get_template(style: ReviewStyle) -> ReviewTemplate:
    """Get template configuration by style."""
    return TEMPLATES.get(style, TEMPLATES[ReviewStyle.FORMAL])


# Base data template (shared across all styles)
DATA_TEMPLATE = """
=== EMPLOYEE PROFILE ===
Name: {name}
Role: {role} ({level})
Department: {department}
Tenure: {years_at_company} years
Review Period: {review_period}

=== PROJECT CONTRIBUTIONS ===
{projects}

=== SKILLS ===
Technical: {technical_skills}
Soft Skills: {soft_skills}

=== QUANTITATIVE METRICS ===
- Code Commits: {commits}
- Pull Request Reviews: {pr_reviews}
- Tasks Completed: {tasks_completed}
- Bugs Fixed: {bugs_fixed}
- Features Delivered: {features_delivered}
- Incidents Resolved: {incidents_resolved}
- Documentation Pages: {documentation_pages}

=== PEER FEEDBACK ===
{peer_feedback}

=== MANAGER ASSESSMENT ===
{manager_notes}

=== PREVIOUS GOALS STATUS ===
{previous_goals}

=== PROFESSIONAL DEVELOPMENT ===
Training Completed: {training_completed}
Mentoring: {mentoring}

=== COLLABORATION ===
Teams Worked With: {teams_collaborated}
Key Contributions: {key_contributions}

=== KNOWN STRENGTHS ===
{strengths}

=== IDENTIFIED GROWTH AREAS ===
{growth_areas}

---

"""
