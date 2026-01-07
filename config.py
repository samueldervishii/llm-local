"""Configuration loader for the performance review generator."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration from environment variables."""

    # MongoDB settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "hr_database")
    EMPLOYEES_COLLECTION: str = os.getenv("EMPLOYEES_COLLECTION", "employees")

    # Model settings
    MODEL_PATH: str = os.getenv("MODEL_PATH", "")
    MODEL_THREADS: int = int(os.getenv("MODEL_THREADS", "6"))
    MODEL_CTX: int = int(os.getenv("MODEL_CTX", "4096"))

    # Output settings
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./output")

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.MODEL_PATH:
            raise ValueError("MODEL_PATH environment variable is required")
        if not os.path.exists(cls.MODEL_PATH):
            raise ValueError(f"Model file not found: {cls.MODEL_PATH}")


config = Config()
