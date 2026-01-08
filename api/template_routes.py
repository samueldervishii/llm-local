"""API routes for managing review templates."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from logging_config import get_logger
from database import MongoDatabase

logger = get_logger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])

# Database instance (initialized on startup)
db: Optional[MongoDatabase] = None


def init_db(db_instance: MongoDatabase) -> None:
    """Initialize database instance."""
    global db
    db = db_instance


# =============================================================================
# MODELS
# =============================================================================


class TemplateCreate(BaseModel):
    """Request model for creating a template."""
    name: str = Field(..., description="Unique template identifier (lowercase, no spaces)")
    display_name: str = Field(..., description="Human-readable template name")
    description: str = Field(..., description="Brief description of the template style")
    best_for: str = Field(..., description="Recommended use cases")
    system_prompt: str = Field(..., description="System prompt for the LLM")
    sections: str = Field(..., description="Section instructions for the LLM")


class TemplateUpdate(BaseModel):
    """Request model for updating a template."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    best_for: Optional[str] = None
    system_prompt: Optional[str] = None
    sections: Optional[str] = None
    active: Optional[bool] = None


class TemplateResponse(BaseModel):
    """Response model for a template."""
    id: str = Field(..., alias="_id")
    name: str
    display_name: str
    description: str
    best_for: str
    active: bool
    system_prompt: Optional[str] = None
    sections: Optional[str] = None

    class Config:
        populate_by_name = True


class TemplateListItem(BaseModel):
    """Simplified template for listing."""
    id: str = Field(..., alias="_id")
    name: str
    display_name: str
    description: str
    best_for: str
    active: bool

    class Config:
        populate_by_name = True


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get(
    "/",
    response_model=list[TemplateListItem],
    summary="List all templates",
    description="Get all active review templates. Use include_inactive=true to see all.",
)
def list_templates(include_inactive: bool = False):
    """List all review templates."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    templates = db.get_all_templates(active_only=not include_inactive)
    return templates


@router.get(
    "/{name}",
    response_model=TemplateResponse,
    summary="Get template by name",
    description="Get full template details including prompts.",
)
def get_template(name: str):
    """Get a specific template by name."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    template = db.get_template(name)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{name}' not found",
        )

    return template


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new template",
    description="Create a custom review template.",
)
def create_template(template: TemplateCreate):
    """Create a new review template."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    # Check if template name already exists
    existing = db.get_template(template.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Template '{template.name}' already exists",
        )

    template_id = db.create_template(template.model_dump())
    logger.info(f"Created template: {template.name}")

    return {
        "message": f"Template '{template.name}' created successfully",
        "id": template_id,
    }


@router.put(
    "/{name}",
    summary="Update a template",
    description="Update an existing template. Only provided fields are updated.",
)
def update_template(name: str, update: TemplateUpdate):
    """Update an existing template."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    # Check if template exists
    existing = db.get_template(name)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{name}' not found",
        )

    # Only update provided fields
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    db.update_template(name, update_data)
    logger.info(f"Updated template: {name}")

    return {"message": f"Template '{name}' updated successfully"}


@router.delete(
    "/{name}",
    summary="Delete a template",
    description="Soft delete a template (sets active=false).",
)
def delete_template(name: str):
    """Delete (deactivate) a template."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    # Prevent deleting default templates
    if name in ["formal", "casual", "technical"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot delete default template '{name}'",
        )

    success = db.delete_template(name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{name}' not found",
        )

    logger.info(f"Deleted template: {name}")
    return {"message": f"Template '{name}' deleted successfully"}
