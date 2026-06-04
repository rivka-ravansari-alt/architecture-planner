"""Text token estimation helpers."""

from __future__ import annotations

from app.config.params import TOKEN_CHARS_PER_TOKEN


def estimate_token_count(text: str) -> int:
    """Rough GPT-style token estimate."""
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, (len(stripped) + (TOKEN_CHARS_PER_TOKEN - 1)) // TOKEN_CHARS_PER_TOKEN)
