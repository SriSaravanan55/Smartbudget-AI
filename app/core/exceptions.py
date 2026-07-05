"""Custom exception types and their FastAPI handlers.

Agents and services raise these domain exceptions instead of HTTPException,
keeping business logic decoupled from the web framework. The handlers here
translate them into consistent JSON error responses.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class SmartBudgetError(Exception):
    """Base class for all domain errors."""
    status_code = 500

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(SmartBudgetError):
    status_code = 404


class ValidationError(SmartBudgetError):
    status_code = 422


class AuthError(SmartBudgetError):
    status_code = 401


class ConflictError(SmartBudgetError):
    status_code = 409


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(SmartBudgetError)
    async def handle_domain_error(request: Request, exc: SmartBudgetError):
        logger.warning("Domain error on %s %s: %s", request.method, request.url.path, exc.message)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
