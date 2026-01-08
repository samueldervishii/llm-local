"""API routes for managing review history."""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from logging_config import get_logger
from database import MongoDatabase

logger = get_logger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])

# Database instance (initialized on startup)
db: Optional[MongoDatabase] = None


def init_db(db_instance: MongoDatabase) -> None:
    """Initialize database instance."""
    global db
    db = db_instance


# =============================================================================
# MODELS
# =============================================================================


class ReviewResponse(BaseModel):
    """Response model for a review record."""
    id: str = Field(..., alias="_id")
    employee_id: Optional[str] = None
    employee_name: str
    template: str
    file_path: str
    pdf_path: Optional[str] = None
    review_period: Optional[str] = None
    status: str
    generated_at: str
    generated_by: Optional[str] = None

    class Config:
        populate_by_name = True


class ReviewStatusUpdate(BaseModel):
    """Request model for updating review status."""
    status: str = Field(..., description="New status: draft, pending_approval, approved, archived")


class ReviewListItem(BaseModel):
    """Simplified review for listing."""
    id: str = Field(..., alias="_id")
    employee_name: str
    template: str
    status: str
    generated_at: str

    class Config:
        populate_by_name = True


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get(
    "/",
    response_model=list[ReviewListItem],
    summary="List all reviews",
    description="Get all generated reviews with optional limit.",
)
def list_reviews(limit: int = 100):
    """List all reviews."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    reviews = db.get_all_reviews(limit=limit)
    # Convert datetime to string for response
    for r in reviews:
        if "generated_at" in r:
            r["generated_at"] = r["generated_at"].isoformat() if hasattr(r["generated_at"], "isoformat") else str(r["generated_at"])
    return reviews


@router.get(
    "/{review_id}",
    response_model=ReviewResponse,
    summary="Get review by ID",
    description="Get full review details by its ID.",
)
def get_review(review_id: str):
    """Get a specific review by ID."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    review = db.get_review(review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review '{review_id}' not found",
        )

    # Convert datetime to string
    if "generated_at" in review:
        review["generated_at"] = review["generated_at"].isoformat() if hasattr(review["generated_at"], "isoformat") else str(review["generated_at"])

    return review


@router.get(
    "/employee/{employee_name}",
    response_model=list[ReviewResponse],
    summary="Get reviews by employee",
    description="Get all reviews for a specific employee.",
)
def get_employee_reviews(employee_name: str):
    """Get all reviews for an employee."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    reviews = db.get_employee_reviews(employee_name)
    # Convert datetime to string for response
    for r in reviews:
        if "generated_at" in r:
            r["generated_at"] = r["generated_at"].isoformat() if hasattr(r["generated_at"], "isoformat") else str(r["generated_at"])

    return reviews


@router.patch(
    "/{review_id}/status",
    summary="Update review status",
    description="Update the status of a review (draft, pending_approval, approved, archived).",
)
def update_review_status(review_id: str, update: ReviewStatusUpdate):
    """Update review status."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    valid_statuses = ["draft", "pending_approval", "approved", "archived"]
    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    success = db.update_review_status(review_id, update.status)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review '{review_id}' not found",
        )

    logger.info(f"Updated review {review_id} status to: {update.status}")
    return {"message": f"Review status updated to '{update.status}'"}


@router.delete(
    "/{review_id}",
    summary="Delete a review",
    description="Permanently delete a review record.",
)
def delete_review(review_id: str):
    """Delete a review."""
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    success = db.delete_review(review_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review '{review_id}' not found",
        )

    logger.info(f"Deleted review: {review_id}")
    return {"message": "Review deleted successfully"}
