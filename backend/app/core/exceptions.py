"""Application-specific exceptions."""

from __future__ import annotations


class AppError(Exception):
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
    pass


class AIValidationError(AppError):
    pass


class ArchitectureGenerationError(AppError):
    pass
