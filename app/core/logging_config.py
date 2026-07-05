"""Structured application logging.

Call configure_logging() once at startup. Every module then does:
    import logging
    logger = logging.getLogger(__name__)
"""
import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(settings.log_level)

    # Avoid duplicate handlers on reload
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Quiet down noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.ERROR)
