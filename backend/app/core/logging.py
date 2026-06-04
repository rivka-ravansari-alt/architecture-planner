"""Structured logging helpers."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class GenerationLogger:
    """Logs generation pipeline steps with a consistent format."""

    def __init__(self, logger_instance: logging.Logger | None = None) -> None:
        self._logger = logger_instance or logger

    def log_step(
        self,
        step: str,
        *,
        project_id: str,
        request_id: str,
        status: str,
        reason: str | None = None,
    ) -> None:
        message = (
            f"generation step={step} status={status} "
            f"project_id={project_id} request_id={request_id}"
        )
        if reason:
            message = f"{message} reason={reason}"
        if status == "failed":
            self._logger.error(message)
        else:
            self._logger.info(message)


class AIClientLogger:
    """Logs AI client operations."""

    def __init__(self, logger_instance: logging.Logger | None = None) -> None:
        self._logger = logger_instance or logger

    def log_started(self, step: str, **details: object) -> None:
        detail_str = " ".join(f"{key}={value}" for key, value in details.items())
        self._logger.info("ai_client step=%s status=started %s", step, detail_str)

    def log_completed(self, step: str, **details: object) -> None:
        detail_str = " ".join(f"{key}={value}" for key, value in details.items())
        self._logger.info("ai_client step=%s status=completed %s", step, detail_str)

    def log_failed(self, step: str, reason: str, prompt: str | None = None) -> None:
        self._logger.error("ai_client step=%s status=failed reason=%s", step, reason)
        if prompt is not None:
            self._logger.error("ai_client step=%s status=failed request_prompt:\n%s", step, prompt)
