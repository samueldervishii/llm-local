"""Onboarding plan generation logic."""

import os
from datetime import datetime
from pathlib import Path

from config import config
from logging_config import get_logger
from llm import LocalLLM
from .onboarding_prompts import ONBOARDING_SYSTEM_PROMPT, format_onboarding_prompt

logger = get_logger(__name__)


class OnboardingGenerator:
    """Generates onboarding plans using local LLM."""

    def __init__(self, llm: LocalLLM):
        self.llm = llm
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Create output directory if needed."""
        Path(config.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, employee_name: str) -> str:
        """Generate output filename."""
        safe_name = employee_name.lower().replace(" ", "_")
        date_str = datetime.now().strftime("%Y%m%d")
        return f"onboarding_{safe_name}_{date_str}.md"

    def _format_document(self, data: dict, content: str) -> str:
        """Format complete onboarding document."""
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

    def generate(self, onboarding_data: dict) -> str:
        """
        Generate onboarding plan.

        Args:
            onboarding_data: Dictionary with new hire info.

        Returns:
            Path to generated file.
        """
        employee_name = onboarding_data.get("employee_name", "Unknown")
        logger.info("Generating onboarding plan")

        prompt = format_onboarding_prompt(onboarding_data)
        content = self.llm.chat(
            system_prompt=ONBOARDING_SYSTEM_PROMPT,
            user_message=prompt,
            temperature=0.3,
            max_tokens=2048,
        )

        document = self._format_document(onboarding_data, content)

        filename = self._generate_filename(employee_name)
        filepath = os.path.join(config.OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(document)

        logger.info(f"Onboarding plan saved to: {filepath}")
        return filepath
