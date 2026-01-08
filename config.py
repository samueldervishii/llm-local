"""Configuration loader for the performance review generator."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory (where config.py lives)
PROJECT_ROOT = Path(__file__).parent.resolve()

load_dotenv()


def _get_cpu_threads() -> int:
    """Get optimal thread count (leaves cores free for other tasks)."""
    try:
        cpu_count = os.cpu_count() or 4
        # Use 60-70% of cores to keep PC responsive
        return max(2, int(cpu_count * 0.65))
    except Exception:
        return 4


class Config:
    """Application configuration from environment variables."""

    # MongoDB settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "hr_database")
    EMPLOYEES_COLLECTION: str = os.getenv("EMPLOYEES_COLLECTION", "employees")

    # Model settings
    MODEL_PATH: str = os.getenv("MODEL_PATH", "")
    MODEL_THREADS: int = int(os.getenv("MODEL_THREADS", str(_get_cpu_threads())))
    MODEL_CTX: int = int(os.getenv("MODEL_CTX", "3072"))  # Balanced: speed + full output
    MODEL_BATCH: int = int(os.getenv("MODEL_BATCH", "512"))  # Batch size for prompt processing
    MODEL_GPU_LAYERS: int = int(os.getenv("MODEL_GPU_LAYERS", "0"))  # 0 = CPU only

    # Cache settings
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"

    # Output settings - always relative to project root
    _output_env = os.getenv("OUTPUT_DIR", "./output")
    OUTPUT_DIR: str = str(PROJECT_ROOT / _output_env.lstrip("./")) if _output_env.startswith("./") else _output_env

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.MODEL_PATH:
            raise ValueError("MODEL_PATH environment variable is required")
        if not os.path.exists(cls.MODEL_PATH):
            raise ValueError(f"Model file not found: {cls.MODEL_PATH}")


config = Config()
