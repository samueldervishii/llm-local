"""API routes for employee management."""

from fastapi import APIRouter, HTTPException, status

from database import MongoDatabase
from logging_config import get_logger
from .models import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    MessageResponse,
    PerformanceMetrics,
    ProjectDetail,
    PreviousGoal,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/employees", tags=["employees"])

# Database instance (connected on startup)
db = MongoDatabase()


def _format_employee_response(employee: dict) -> EmployeeResponse:
    """Convert MongoDB document to response model."""
    # Handle projects (could be old format or new format)
    projects_raw = employee.get("projects", [])
    if projects_raw and isinstance(projects_raw[0], dict):
        projects = [ProjectDetail(**p) for p in projects_raw]
    else:
        projects = []

    # Handle previous goals
    goals_raw = employee.get("previous_goals", [])
    if goals_raw and isinstance(goals_raw[0], dict):
        previous_goals = [PreviousGoal(**g) for g in goals_raw]
    else:
        previous_goals = []

    return EmployeeResponse(
        id=str(employee.get("_id", "")),
        name=employee.get("name", ""),
        role=employee.get("role", ""),
        department=employee.get("department", ""),
        level=employee.get("level", ""),
        years_at_company=employee.get("years_at_company", 0),
        review_period=employee.get("review_period", ""),
        projects=projects,
        technical_skills=employee.get("technical_skills", []),
        soft_skills=employee.get("soft_skills", []),
        metrics=PerformanceMetrics(**employee.get("metrics", {})),
        peer_feedback=employee.get("peer_feedback", []),
        manager_notes=employee.get("manager_notes", ""),
        previous_goals=previous_goals,
        training_completed=employee.get("training_completed", []),
        mentoring=employee.get("mentoring", ""),
        teams_collaborated=employee.get("teams_collaborated", []),
        key_contributions=employee.get("key_contributions", []),
        strengths=employee.get("strengths", []),
        growth_areas=employee.get("growth_areas", []),
    )


@router.post(
    "/",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employee",
    description="Add a new employee with their performance data to the database.",
)
def create_employee(employee: EmployeeCreate):
    """Create a new employee record."""
    logger.info("Creating new employee record")

    if db.employee_exists(employee.name):
        logger.warning("Employee already exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee '{employee.name}' already exists",
        )

    # Serialize all nested models properly
    employee_data = employee.model_dump()

    inserted_id = db.insert_employee(employee_data)
    logger.info(f"Employee created successfully (ID: {inserted_id})")

    # Audit log
    db.log_action(
        action="create",
        resource_type="employee",
        resource_id=inserted_id,
        details={"name": employee.name, "department": employee.department},
        user="api",
    )

    return MessageResponse(
        message=f"Employee '{employee.name}' created successfully",
        id=inserted_id,
    )


@router.get(
    "/",
    response_model=list[EmployeeResponse],
    summary="List all employees",
    description="Retrieve all employees from the database.",
)
def list_employees():
    """Get all employees."""
    logger.debug("Fetching all employees")
    employees = db.get_all_employees()
    logger.info(f"Retrieved {len(employees)} employees")
    return [_format_employee_response(emp) for emp in employees]


@router.get(
    "/{name}",
    response_model=EmployeeResponse,
    summary="Get employee by name",
    description="Retrieve a specific employee by their name.",
)
def get_employee(name: str):
    """Get a single employee by name."""
    logger.debug("Fetching employee record")
    employee = db.get_employee(name)
    if not employee:
        logger.warning("Employee not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{name}' not found",
        )
    logger.info("Retrieved employee record")
    return _format_employee_response(employee)


@router.put(
    "/{name}",
    response_model=MessageResponse,
    summary="Update employee",
    description="Update an existing employee's data.",
)
def update_employee(name: str, employee: EmployeeUpdate):
    """Update an existing employee."""
    logger.info("Updating employee record")

    if not db.employee_exists(name):
        logger.warning("Employee not found for update")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{name}' not found",
        )

    update_data = employee.model_dump(exclude_unset=True)
    if "metrics" in update_data and update_data["metrics"]:
        update_data["metrics"] = employee.metrics.model_dump()

    if not update_data:
        logger.warning("No fields to update")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    db.update_employee(name, update_data)
    logger.info("Employee updated successfully")

    # Audit log
    db.log_action(
        action="update",
        resource_type="employee",
        details={"name": name, "fields_updated": list(update_data.keys())},
        user="api",
    )

    return MessageResponse(message=f"Employee '{name}' updated successfully")


@router.delete(
    "/{name}",
    response_model=MessageResponse,
    summary="Delete employee",
    description="Remove an employee from the database.",
)
def delete_employee(name: str):
    """Delete an employee."""
    logger.info("Deleting employee record")

    if not db.delete_employee(name):
        logger.warning("Employee not found for deletion")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{name}' not found",
        )

    logger.info("Employee deleted successfully")

    # Audit log
    db.log_action(
        action="delete",
        resource_type="employee",
        details={"name": name},
        user="api",
    )

    return MessageResponse(message=f"Employee '{name}' deleted successfully")
