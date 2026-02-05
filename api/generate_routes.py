"""API routes for document generation using LLM."""

import os
from datetime import datetime
from enum import Enum
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config import config
from logging_config import get_logger
from database import MongoDatabase
from llm import LocalLLM
from encryption import encrypt_document, decrypt_document
from generator.prompts import format_employee_prompt
from generator.templates import ReviewStyle, DATA_TEMPLATE
from generator.pdf_export import markdown_to_pdf
from generator.onboarding_prompts import (
    ONBOARDING_SYSTEM_PROMPT,
    format_onboarding_prompt,
)
from .models import OnboardingRequest

logger = get_logger(__name__)

router = APIRouter(prefix="/generate", tags=["generation"])


def _validate_filename(filename: str) -> str:
    """
    Validate and sanitize filename to prevent path traversal attacks.

    Args:
        filename: User-provided filename.

    Returns:
        Safe filepath within OUTPUT_DIR.

    Raises:
        HTTPException: If filename is invalid or attempts path traversal.
    """
    # Get just the base filename, stripping any path components
    safe_name = os.path.basename(filename)

    # Reject empty or hidden files
    if not safe_name or safe_name.startswith('.'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
        )

    # Build the full path
    filepath = os.path.join(config.OUTPUT_DIR, safe_name)

    # Resolve to absolute path and verify it's within OUTPUT_DIR
    abs_filepath = os.path.abspath(filepath)
    abs_output_dir = os.path.abspath(config.OUTPUT_DIR)

    if not abs_filepath.startswith(abs_output_dir + os.sep):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
        )

    return abs_filepath

# Shared instances (initialized on startup)
llm: Optional[LocalLLM] = None
db: Optional[MongoDatabase] = None


class ReviewResponse(BaseModel):
    """Response model for generated review."""

    success: bool
    review_id: str
    employee_name: str
    file_path: str
    pdf_path: Optional[str] = None
    template: str
    message: str
    generated_at: str


class OnboardingResponse(BaseModel):
    """Response model for generated onboarding plan."""

    success: bool
    employee_name: str
    file_path: str
    message: str
    generated_at: str


class GenerationError(BaseModel):
    """Error response model."""

    success: bool = False
    error: str
    detail: Optional[str] = None


def init_services(llm_instance: LocalLLM, db_instance: MongoDatabase) -> None:
    """
    Initialize shared service instances.

    Args:
        llm_instance: Loaded LLM instance.
        db_instance: Connected database instance.
    """
    global llm, db
    llm = llm_instance
    db = db_instance
    logger.info("Generation services initialized")


def _get_template_from_db(template_name: str) -> dict:
    """Fetch template from database, fall back to defaults if not found."""
    template = db.get_template(template_name)
    if template:
        return template

    # Fallback to hardcoded defaults
    logger.warning(f"Template '{template_name}' not found in DB, using default")
    from generator.templates import get_template, ReviewStyle
    style = ReviewStyle(template_name)
    default = get_template(style)
    return {
        "name": template_name,
        "system_prompt": default.system_prompt,
        "sections": default.sections,
    }


def _generate_review_content(employee: dict, template_name: str = "formal") -> str:
    """Generate review content using LLM with template from database."""
    template = _get_template_from_db(template_name)
    system_prompt = template["system_prompt"]
    sections = template["sections"]

    # Build the full prompt with employee data and sections
    prompt = format_employee_prompt(employee, ReviewStyle(template_name))

    return llm.chat(
        system_prompt=system_prompt,
        user_message=prompt,
        temperature=0.3,
        max_tokens=2048,
    )


def _generate_onboarding_content(data: dict) -> str:
    """Generate onboarding content using LLM."""
    prompt = format_onboarding_prompt(data)
    return llm.chat(
        system_prompt=ONBOARDING_SYSTEM_PROMPT,
        user_message=prompt,
        temperature=0.3,
        max_tokens=2048,
    )


def _format_review_document(employee: dict, content: str) -> str:
    """Format the complete review document."""
    header = f"""# Performance Review - DRAFT

**Employee:** {employee.get("name", "Unknown")}
**Role:** {employee.get("role", "Unknown")}
**Department:** {employee.get("department", "Unknown")}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Status:** DRAFT - Requires HR Review

---

"""
    footer = """

---

## Important Notice

This performance review is a **DRAFT** generated by an automated system.
It requires thorough review and approval by HR and the employee's direct manager
before being shared with the employee or used for any official purposes.

**This document should not be considered final until approved by HR.**
"""
    return header + content + footer


def _format_onboarding_document(data: dict, content: str) -> str:
    """Format the complete onboarding document."""
    header = f"""# Onboarding Plan

**New Hire:** {data.get("employee_name", "Unknown")}
**Role:** {data.get("role", "Unknown")}
**Department:** {data.get("department", "Unknown")}
**Start Date:** {data.get("start_date", "TBD")}
**Manager:** {data.get("manager_name", "Unknown")}
**Buddy:** {data.get("buddy_name", "Not assigned")}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
    footer = """

---

*This onboarding plan was auto-generated. Please review and customize as needed.*
"""
    return header + content + footer


def _save_document(content: str, filename: str) -> str:
    """Save encrypted document to output directory."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(config.OUTPUT_DIR, filename)
    # Encrypt sensitive employee data before saving
    encrypted_path = encrypt_document(content, filepath)
    return encrypted_path


@router.post(
    "/review/{employee_name}",
    response_model=ReviewResponse,
    responses={
        404: {"model": GenerationError, "description": "Employee not found"},
        500: {"model": GenerationError, "description": "Generation failed"},
    },
    summary="Generate performance review",
    description="Generate a performance review for a specific employee using the local LLM.",
)
def generate_review(
    employee_name: str,
    template: ReviewStyle = Query(
        default=ReviewStyle.FORMAL,
        description="Review style: formal (corporate), casual (friendly), technical (engineering-focused)"
    ),
    export_pdf: bool = Query(
        default=False,
        description="Also generate a PDF version of the review"
    ),
):
    """Generate a performance review for an employee."""
    logger.info(f"Review generation requested (template: {template.value}, pdf: {export_pdf})")

    # Check if services are initialized
    if not llm or not db:
        logger.error("Services not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Generation services not available",
        )

    # Fetch employee
    logger.debug("Fetching employee data")
    employee = db.get_employee(employee_name)

    if not employee:
        logger.warning("Employee not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{employee_name}' not found",
        )

    try:
        # Generate review
        logger.info(f"Generating review content using {template.value} template")
        start_time = datetime.now()

        content = _generate_review_content(employee, template.value)
        document = _format_review_document(employee, content)

        # Save to file
        safe_name = employee_name.lower().replace(" ", "_")
        date_str = datetime.now().strftime("%Y%m%d")
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"review_{safe_name}_{template.value}_{date_str}_{timestamp}.md"
        filepath = _save_document(document, filename)

        # Generate PDF if requested
        pdf_path = None
        if export_pdf:
            logger.info("Generating PDF export")
            pdf_filename = f"review_{safe_name}_{template.value}_{date_str}_{timestamp}.pdf"
            pdf_filepath = os.path.join(config.OUTPUT_DIR, pdf_filename)
            markdown_to_pdf(document, pdf_filepath, template.value)
            pdf_path = pdf_filepath
            logger.info("PDF generated successfully")

        # Save review to database
        employee_id = employee.get("_id")
        review_data = {
            "employee_id": employee_id if isinstance(employee_id, ObjectId) else ObjectId(employee_id) if employee_id else None,
            "employee_name": employee_name,
            "template": template.value,
            "file_path": filepath,
            "pdf_path": pdf_path,
            "review_period": employee.get("review_period", "Current Quarter"),
            "generated_by": "api",
        }
        review_id = db.create_review(review_data)
        logger.info(f"Review saved to database: {review_id}")

        # Link review to employee
        db.add_review_to_employee(employee_name, review_id)
        logger.info(f"Review linked to employee (review_id: {review_id})")

        # Audit log
        db.log_action(
            action="generate",
            resource_type="review",
            resource_id=review_id,
            details={"template": template.value, "pdf_exported": export_pdf},
            user="api",
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Review generated successfully in {elapsed:.2f}s")

        return ReviewResponse(
            success=True,
            review_id=review_id,
            employee_name=employee_name,
            file_path=filepath,
            pdf_path=pdf_path,
            template=template.value,
            message=f"Performance review ({template.value}) generated successfully in {elapsed:.2f}s",
            generated_at=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to generate review: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate review: {str(e)}",
        )


@router.post(
    "/onboarding",
    response_model=OnboardingResponse,
    responses={
        500: {"model": GenerationError, "description": "Generation failed"},
    },
    summary="Generate onboarding plan",
    description="Generate an onboarding plan for a new hire using the local LLM.",
)
def generate_onboarding(request: OnboardingRequest):
    """Generate an onboarding plan for a new hire."""
    logger.info("Onboarding generation requested")

    # Check if services are initialized
    if not llm:
        logger.error("LLM service not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Generation services not available",
        )

    try:
        # Generate onboarding plan
        logger.info("Generating onboarding content")
        start_time = datetime.now()

        data = request.model_dump()
        content = _generate_onboarding_content(data)
        document = _format_onboarding_document(data, content)

        # Save to file
        safe_name = request.employee_name.lower().replace(" ", "_")
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"onboarding_{safe_name}_{date_str}.md"
        filepath = _save_document(document, filename)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Onboarding plan generated in {elapsed:.2f}s")

        return OnboardingResponse(
            success=True,
            employee_name=request.employee_name,
            file_path=filepath,
            message=f"Onboarding plan generated successfully in {elapsed:.2f}s",
            generated_at=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to generate onboarding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate onboarding plan: {str(e)}",
        )


# =============================================================================
# PDF EXPORT ENDPOINTS
# =============================================================================


class ConvertPdfRequest(BaseModel):
    """Request model for converting markdown to PDF."""
    filename: str = Field(..., description="Filename of the markdown file in output directory (e.g., review_john_doe_formal_20260108.md)")
    template: ReviewStyle = Field(default=ReviewStyle.FORMAL, description="PDF style template")


class ConvertPdfResponse(BaseModel):
    """Response model for PDF conversion."""
    success: bool
    pdf_path: str
    message: str


@router.post(
    "/convert-to-pdf",
    response_model=ConvertPdfResponse,
    summary="Convert markdown to PDF",
    description="Convert an existing markdown review file to a styled PDF.",
)
def convert_to_pdf(request: ConvertPdfRequest):
    """Convert an existing markdown file to PDF."""
    # Validate and sanitize filename to prevent path traversal
    markdown_path = _validate_filename(request.filename)
    logger.info("PDF conversion requested")

    # Check for encrypted version
    encrypted_path = markdown_path + '.enc' if not markdown_path.endswith('.enc') else markdown_path

    if os.path.exists(encrypted_path):
        # Decrypt and read content
        try:
            content = decrypt_document(encrypted_path)
        except Exception as e:
            logger.error(f"Failed to decrypt file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to decrypt file: {str(e)}",
            )
    elif os.path.exists(markdown_path):
        # Legacy unencrypted file
        with open(markdown_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        # List available files to help user
        available = [f for f in os.listdir(config.OUTPUT_DIR) if f.endswith(('.md', '.md.enc'))] if os.path.exists(config.OUTPUT_DIR) else []
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {os.path.basename(request.filename)}. Available files: {available}",
        )

    try:
        # Generate PDF path (strip .enc if present)
        base_path = markdown_path.rstrip('.enc') if markdown_path.endswith('.enc') else markdown_path
        pdf_path = base_path.rsplit(".", 1)[0] + ".pdf"

        # Convert to PDF
        markdown_to_pdf(content, pdf_path, request.template.value)

        logger.info("PDF created successfully")
        return ConvertPdfResponse(
            success=True,
            pdf_path=pdf_path,
            message=f"PDF created successfully with {request.template.value} template",
        )

    except Exception as e:
        logger.error(f"Failed to convert to PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert to PDF: {str(e)}",
        )


@router.get(
    "/download/{filename}",
    summary="Download generated file",
    description="Download a generated review or onboarding file (markdown or PDF). Encrypted files are automatically decrypted.",
)
def download_file(filename: str):
    """Download a generated file from the output directory."""
    # Validate and sanitize filename to prevent path traversal
    filepath = _validate_filename(filename)

    # Check for encrypted version if original doesn't exist
    encrypted_path = filepath + '.enc' if not filepath.endswith('.enc') else filepath

    if os.path.exists(encrypted_path):
        # Decrypt and return content
        try:
            decrypted_content = decrypt_document(encrypted_path)

            # Determine the original filename (remove .enc extension for response)
            original_filename = filename.rstrip('.enc')

            # Determine media type based on original extension
            if original_filename.endswith(".pdf"):
                media_type = "application/pdf"
            elif original_filename.endswith(".md"):
                media_type = "text/markdown"
            else:
                media_type = "text/plain"

            from fastapi.responses import Response
            return Response(
                content=decrypted_content,
                media_type=media_type,
                headers={"Content-Disposition": f'attachment; filename="{original_filename}"'}
            )
        except Exception as e:
            logger.error(f"Failed to decrypt file {filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to decrypt file: {str(e)}",
            )
    elif os.path.exists(filepath):
        # File exists but is not encrypted (legacy or PDF)
        if filename.endswith(".pdf"):
            media_type = "application/pdf"
        elif filename.endswith(".md"):
            media_type = "text/markdown"
        else:
            media_type = "application/octet-stream"

        return FileResponse(
            path=filepath,
            filename=filename,
            media_type=media_type,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {os.path.basename(filename)}",
        )


@router.get(
    "/templates",
    summary="List available templates",
    description="Get list of available review templates with descriptions.",
)
def list_templates():
    """List all available review templates."""
    return {
        "templates": [
            {
                "name": "formal",
                "description": "Traditional corporate HR style - professional, objective, third-person",
                "best_for": "Official HR records, large corporations, formal review processes",
            },
            {
                "name": "casual",
                "description": "Modern friendly style - warm, encouraging, first-person",
                "best_for": "Startups, small teams, regular check-ins",
            },
            {
                "name": "technical",
                "description": "Engineering-focused style - metrics-heavy, precise, technical",
                "best_for": "Engineering teams, technical roles, performance benchmarking",
            },
        ]
    }


# =============================================================================
# COMMENTED OUT: Generate all reviews endpoint
# Uncomment when needed - be aware this can take a long time with many employees
# =============================================================================
#
# class BatchReviewResponse(BaseModel):
#     """Response model for batch review generation."""
#     success: bool
#     total_employees: int
#     generated: int
#     failed: int
#     results: list[dict]
#     elapsed_seconds: float
#
#
# @router.post(
#     "/reviews/all",
#     response_model=BatchReviewResponse,
#     summary="Generate all reviews",
#     description="Generate performance reviews for all employees. Warning: This can take a long time.",
# )
# def generate_all_reviews():
#     """Generate reviews for all employees in the database."""
#     logger.info("Batch review generation requested")
#
#     if not llm or not db:
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Generation services not available",
#         )
#
#     employees = db.get_all_employees()
#     if not employees:
#         return BatchReviewResponse(
#             success=True,
#             total_employees=0,
#             generated=0,
#             failed=0,
#             results=[],
#             elapsed_seconds=0,
#         )
#
#     logger.info(f"Starting batch generation for {len(employees)} employees")
#     start_time = datetime.now()
#     results = []
#     generated = 0
#     failed = 0
#
#     for employee in employees:
#         name = employee.get("name", "Unknown")
#         try:
#             logger.info(f"Generating review for: {name}")
#             content = _generate_review_content(employee)
#             document = _format_review_document(employee, content)
#
#             safe_name = name.lower().replace(" ", "_")
#             date_str = datetime.now().strftime("%Y%m%d")
#             filename = f"review_{safe_name}_{date_str}.md"
#             filepath = _save_document(document, filename)
#
#             results.append({"name": name, "success": True, "file": filepath})
#             generated += 1
#             logger.info(f"Review generated for: {name}")
#
#         except Exception as e:
#             logger.error(f"Failed to generate review for {name}: {str(e)}")
#             results.append({"name": name, "success": False, "error": str(e)})
#             failed += 1
#
#     elapsed = (datetime.now() - start_time).total_seconds()
#     logger.info(f"Batch generation complete: {generated} success, {failed} failed, {elapsed:.2f}s")
#
#     return BatchReviewResponse(
#         success=failed == 0,
#         total_employees=len(employees),
#         generated=generated,
#         failed=failed,
#         results=results,
#         elapsed_seconds=elapsed,
#     )
