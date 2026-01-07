"""Prompts for onboarding plan generation."""

ONBOARDING_SYSTEM_PROMPT = """You are an HR assistant creating onboarding plans.
Generate practical, detailed checklists for new employee onboarding.
Be specific with tasks and timelines. Keep it actionable."""

ONBOARDING_TEMPLATE = """Create a detailed onboarding plan for this new hire:

=== NEW HIRE INFO ===
Name: {employee_name}
Role: {role}
Department: {department}
Start Date: {start_date}
Manager: {manager_name}
Buddy/Mentor: {buddy_name}

=== EQUIPMENT NEEDED ===
{equipment}

=== SYSTEMS ACCESS REQUIRED ===
{systems_access}

=== REQUIRED TRAINING ===
{training_required}

=== TEAM MEMBERS TO MEET ===
{team_members}

---

Generate a structured onboarding plan with these sections:

## PRE-START (Before Day 1)
- [ ] Checklist of tasks for HR/IT/Manager before employee arrives

## DAY 1
- [ ] Hour-by-hour schedule for first day

## WEEK 1
- [ ] Daily goals and meetings for the first week

## MONTH 1 (Days 8-30)
- [ ] Weekly milestones and objectives

## 30-60-90 DAY GOALS
- Clear success metrics for each milestone

## KEY MEETINGS TO SCHEDULE
- List of essential 1:1s with names and purpose

## RESOURCES & LINKS
- Documentation and tools they should bookmark

Use markdown checkboxes [ ] for action items."""


def format_onboarding_prompt(data: dict) -> str:
    """Format onboarding data into prompt."""

    equipment = "\n".join(f"- {item}" for item in data.get("equipment", [])) or "- TBD"
    systems = "\n".join(f"- {sys}" for sys in data.get("systems_access", [])) or "- TBD"
    training = "\n".join(f"- {t}" for t in data.get("training_required", [])) or "- None specified"
    team = "\n".join(f"- {member}" for member in data.get("team_members", [])) or "- TBD"

    return ONBOARDING_TEMPLATE.format(
        employee_name=data.get("employee_name", "Unknown"),
        role=data.get("role", "Unknown"),
        department=data.get("department", "Unknown"),
        start_date=data.get("start_date", "TBD"),
        manager_name=data.get("manager_name", "Unknown"),
        buddy_name=data.get("buddy_name", "Not assigned"),
        equipment=equipment,
        systems_access=systems,
        training_required=training,
        team_members=team,
    )
