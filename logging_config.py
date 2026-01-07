"""Logging configuration for the HR Document Generator."""

import logging
import sys

# Log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Track if logging has been configured
_logging_configured = False


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure application logging.

    Args:
        level: Logging level (default: INFO)

    Returns:
        Configured root logger.
    """
    global _logging_configured

    # Prevent duplicate configuration
    if _logging_configured:
        return logging.getLogger()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # Get our app logger (not root to avoid duplicates)
    app_logger = logging.getLogger("api")
    app_logger.setLevel(level)

    # Clear existing handlers and add new one
    app_logger.handlers.clear()
    app_logger.addHandler(console_handler)
    app_logger.propagate = False  # Prevent duplicate logs

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    _logging_configured = True

    return app_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance.
    """
    logger = logging.getLogger(name)
    logger.propagate = False  # Prevent duplicate logs
    return logger
