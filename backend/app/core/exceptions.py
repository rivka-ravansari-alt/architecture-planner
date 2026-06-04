"""Application-specific exceptions."""

from __future__ import annotations


class AppError(Exception):
    """Base exception for domain and service errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    pass


class ForbiddenError(AppError):
    pass


class UnauthorizedError(AppError):
    pass


class ServiceUnavailableError(AppError):
    pass


class BadRequestError(AppError):
    pass


class AIClientError(AppError):
    """Raised when the AI provider call fails."""


class AIValidationError(AppError):
    """Raised when the AI response is missing or invalid."""


class ArchitectureGenerationError(AppError):
    """Raised when the generation pipeline fails."""
