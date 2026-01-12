"""API routes for bulk operations."""

import csv
import io
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from pydantic import BaseModel, Field

from logging_config import get_logger
from database import MongoDatabase

logger = get_logger(__name__)

router = APIRouter(prefix="/bulk", tags=["bulk"])

# Database instance (initialized on startup)
db: Optional[MongoDatabase] = None


def init_db(db_instance: MongoDatabase) -> None:
    """Initialize database instance."""
    global db
    db = db_instance


# =============================================================================
# MODELS
# =============================================================================


class BulkImportResponse(BaseModel):
    """Response model for bulk import."""
    success: bool
    inserted: int
    skipped: int
    errors: list[dict] = Field(default_factory=list)
    message: str


class EmployeeImportItem(BaseModel):
    """Single employee for JSON import."""
    name: str
    role: str
    department: str
    level: Optional[str] = "mid"
    years_at_company: Optional[float] = 0
    review_period: Optional[str] = None
    technical_skills: Optional[list[str]] = Field(default_factory=list)
    soft_skills: Optional[list[str]] = Field(default_factory=list)


class BulkImportRequest(BaseModel):
    """Request model for JSON bulk import."""
    employees: list[EmployeeImportItem]


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post(
    "/employees/json",
    response_model=BulkImportResponse,
    summary="Bulk import employees from JSON",
    description="Import multiple employees from a JSON array.",
)
def bulk_import_json(request: BulkImportRequest):
    """Bulk import employees from JSON."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    employees = [emp.model_dump() for emp in request.employees]
    logger.info(f"Bulk import requested: {len(employees)} employees")

    results = db.bulk_insert_employees(employees)

    # Log the action
    db.log_action(
        action="bulk_create",
        resource_type="employee",
        details={
            "total": len(employees),
            "inserted": results["inserted"],
            "skipped": results["skipped"],
        },
        user="api",
    )

    logger.info(f"Bulk import complete: {results['inserted']} inserted, {results['skipped']} skipped")

    return BulkImportResponse(
        success=results["inserted"] > 0,
        inserted=results["inserted"],
        skipped=results["skipped"],
        errors=results["errors"],
        message=f"Imported {results['inserted']} employees, skipped {results['skipped']}",
    )


@router.post(
    "/employees/csv",
    response_model=BulkImportResponse,
    summary="Bulk import employees from CSV",
    description="Import multiple employees from a CSV file. Required columns: name, role, department. Optional: level, years_at_company, review_period.",
)
async def bulk_import_csv(file: UploadFile = File(...)):
    """Bulk import employees from CSV file."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV",
        )

    try:
        # Read and parse CSV
        content = await file.read()
        decoded = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))

        employees = []
        for row in reader:
            # Map CSV columns to employee fields
            emp = {
                "name": row.get("name", "").strip(),
                "role": row.get("role", "").strip(),
                "department": row.get("department", "").strip(),
                "level": row.get("level", "mid").strip() or "mid",
                "years_at_company": float(row.get("years_at_company", 0) or 0),
                "review_period": row.get("review_period", "").strip() or None,
            }

            # Handle optional list fields
            if "technical_skills" in row and row["technical_skills"]:
                emp["technical_skills"] = [s.strip() for s in row["technical_skills"].split(",")]
            if "soft_skills" in row and row["soft_skills"]:
                emp["soft_skills"] = [s.strip() for s in row["soft_skills"].split(",")]

            employees.append(emp)

        logger.info(f"CSV bulk import requested: {len(employees)} employees from {file.filename}")

        results = db.bulk_insert_employees(employees)

        # Log the action
        db.log_action(
            action="bulk_create",
            resource_type="employee",
            details={
                "source": "csv",
                "filename": file.filename,
                "total": len(employees),
                "inserted": results["inserted"],
                "skipped": results["skipped"],
            },
            user="api",
        )

        logger.info(f"CSV bulk import complete: {results['inserted']} inserted, {results['skipped']} skipped")

        return BulkImportResponse(
            success=results["inserted"] > 0,
            inserted=results["inserted"],
            skipped=results["skipped"],
            errors=results["errors"],
            message=f"Imported {results['inserted']} employees from CSV, skipped {results['skipped']}",
        )

    except csv.Error as e:
        logger.error(f"CSV parsing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV format: {e}",
        )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded",
        )
    except Exception as e:
        logger.error(f"Bulk import error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {e}",
        )
