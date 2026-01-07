"""System prompts and templates for review generation."""

SYSTEM_PROMPT = """You are an HR professional assistant drafting performance reviews.
Generate professional, constructive, and balanced content.
Be SPECIFIC - reference exact numbers, project names, and quotes from the data.
Keep the tone professional yet encouraging. Focus on measurable achievements."""

REVIEW_TEMPLATE = """Generate a performance review based on this employee data.

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

Generate these sections using the data above. Be specific and cite numbers/names:

1. PERFORMANCE SUMMARY (2-3 paragraphs - reference specific metrics and projects)

2. KEY ACHIEVEMENTS (4-5 bullets - include measurable impact from projects)

3. GOAL REVIEW (assess each previous goal's status with context)

4. AREAS FOR GROWTH (2-3 specific areas based on growth_areas and feedback)

5. GOALS FOR NEXT QUARTER (3-4 SMART goals - specific, measurable, achievable)

6. TECHNICAL INTERVIEW QUESTIONS (3 questions based on their role and tech stack)

7. SOFT SKILL INTERVIEW QUESTIONS (3 questions based on their level and growth areas)

Use markdown formatting with ## headers."""


def format_employee_prompt(employee: dict) -> str:
    """
    Format employee data into the review prompt template.

    Args:
        employee: Employee document from MongoDB.

    Returns:
        Formatted prompt string.
    """
    metrics = employee.get("metrics", {})

    # Format detailed projects
    projects_list = employee.get("projects", [])
    if projects_list and isinstance(projects_list[0], dict):
        projects = "\n".join(
            f"- {p.get('name', 'Unknown')} (Role: {p.get('role', 'N/A')})\n"
            f"  Impact: {p.get('impact', 'N/A')}\n"
            f"  Tech: {', '.join(p.get('technologies', []))}"
            for p in projects_list
        ) or "- No projects listed"
    else:
        # Fallback for old simple format
        projects = "\n".join(f"- {p}" for p in projects_list) or "- No projects listed"

    # Format skills
    technical_skills = ", ".join(employee.get("technical_skills", [])) or "None listed"
    soft_skills = ", ".join(employee.get("soft_skills", [])) or "None listed"

    # Format peer feedback
    peer_feedback = "\n".join(
        f"- \"{fb}\"" for fb in employee.get("peer_feedback", [])
    ) or "- No peer feedback available"

    # Format previous goals
    prev_goals = employee.get("previous_goals", [])
    if prev_goals and isinstance(prev_goals[0], dict):
        previous_goals = "\n".join(
            f"- {g.get('goal', 'N/A')} → Status: {g.get('status', 'N/A')}"
            f"{' (' + g.get('notes') + ')' if g.get('notes') else ''}"
            for g in prev_goals
        ) or "- No previous goals recorded"
    else:
        previous_goals = "- No previous goals recorded"

    # Format training
    training = ", ".join(employee.get("training_completed", [])) or "None this period"

    # Format teams collaborated
    teams = ", ".join(employee.get("teams_collaborated", [])) or "None listed"

    # Format key contributions
    contributions = "\n".join(
        f"- {c}" for c in employee.get("key_contributions", [])
    ) or "- None listed"

    # Format strengths
    strengths = "\n".join(
        f"- {s}" for s in employee.get("strengths", [])
    ) or "- None identified"

    # Format growth areas
    growth_areas = "\n".join(
        f"- {g}" for g in employee.get("growth_areas", [])
    ) or "- None identified"

    return REVIEW_TEMPLATE.format(
        name=employee.get("name", "Unknown"),
        role=employee.get("role", "Unknown"),
        level=employee.get("level", "N/A"),
        department=employee.get("department", "Unknown"),
        years_at_company=employee.get("years_at_company", 0),
        review_period=employee.get("review_period", "Current Quarter"),
        projects=projects,
        technical_skills=technical_skills,
        soft_skills=soft_skills,
        commits=metrics.get("commits", 0),
        pr_reviews=metrics.get("pr_reviews", 0),
        tasks_completed=metrics.get("tasks_completed", 0),
        bugs_fixed=metrics.get("bugs_fixed", 0),
        features_delivered=metrics.get("features_delivered", 0),
        incidents_resolved=metrics.get("incidents_resolved", 0),
        documentation_pages=metrics.get("documentation_pages", 0),
        peer_feedback=peer_feedback,
        manager_notes=employee.get("manager_notes", "No manager notes available"),
        previous_goals=previous_goals,
        training_completed=training,
        mentoring=employee.get("mentoring", "None recorded"),
        teams_collaborated=teams,
        key_contributions=contributions,
        strengths=strengths,
        growth_areas=growth_areas,
    )
