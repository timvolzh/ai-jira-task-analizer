from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def configure_logging(log_level: str, run_id: str) -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(run_id=run_id)


def get_logger() -> structlog.stdlib.BoundLogger:
    return structlog.get_logger()


def log_exception(logger: structlog.stdlib.BoundLogger, message: str, **kwargs: Any) -> None:
    logger.error(message, **kwargs, exc_info=True)
