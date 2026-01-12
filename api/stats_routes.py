"""API routes for statistics and audit logs."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from logging_config import get_logger
from database import MongoDatabase

logger = get_logger(__name__)

router = APIRouter(tags=["statistics"])

# Database instance (initialized on startup)
db: Optional[MongoDatabase] = None


def init_db(db_instance: MongoDatabase) -> None:
    """Initialize database instance."""
    global db
    db = db_instance


# =============================================================================
# MODELS
# =============================================================================


class EmployeeStats(BaseModel):
    """Employee statistics."""
    total: int
    by_department: dict[str, int]
    by_level: dict[str, int]


class ReviewStats(BaseModel):
    """Review statistics."""
    total: int
    by_status: dict[str, int]
    by_template: dict[str, int]


class TemplateStats(BaseModel):
    """Template statistics."""
    total: int
    active: int


class AuditStats(BaseModel):
    """Audit log statistics."""
    total: int


class StatisticsResponse(BaseModel):
    """Full statistics response."""
    employees: EmployeeStats
    reviews: ReviewStats
    templates: TemplateStats
    audit_logs: AuditStats


class AuditLogEntry(BaseModel):
    """Single audit log entry."""
    id: str = Field(..., alias="_id")
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: dict = Field(default_factory=dict)
    user: str
    timestamp: str

    class Config:
        populate_by_name = True


# =============================================================================
# STATISTICS ENDPOINTS
# =============================================================================


@router.get(
    "/stats",
    response_model=StatisticsResponse,
    summary="Get system statistics",
    description="Get aggregated statistics about employees, reviews, templates, and audit logs.",
)
def get_statistics():
    """Get system statistics."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    stats = db.get_statistics()
    logger.info("Statistics retrieved")

    return StatisticsResponse(
        employees=EmployeeStats(**stats["employees"]),
        reviews=ReviewStats(**stats["reviews"]),
        templates=TemplateStats(**stats["templates"]),
        audit_logs=AuditStats(**stats["audit_logs"]),
    )


# =============================================================================
# AUDIT LOG ENDPOINTS
# =============================================================================


@router.get(
    "/audit-logs",
    response_model=list[AuditLogEntry],
    summary="Get audit logs",
    description="Get audit logs with optional filtering by resource type and action.",
)
def get_audit_logs(
    limit: int = Query(default=100, le=1000, description="Maximum number of logs to return"),
    resource_type: Optional[str] = Query(default=None, description="Filter by resource type (employee, review, template)"),
    action: Optional[str] = Query(default=None, description="Filter by action (create, update, delete, generate, bulk_create)"),
):
    """Get audit logs."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    logs = db.get_audit_logs(limit=limit, resource_type=resource_type, action=action)

    # Convert timestamps to ISO format strings
    for log in logs:
        if "timestamp" in log:
            log["timestamp"] = log["timestamp"].isoformat() if hasattr(log["timestamp"], "isoformat") else str(log["timestamp"])

    logger.info(f"Retrieved {len(logs)} audit logs")
    return logs
