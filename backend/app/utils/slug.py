"""String slug helpers."""

from __future__ import annotations

import re

from app.config.params import SLUG_MAX_LENGTH


def slugify(
    value: str,
    *,
    max_length: int = SLUG_MAX_LENGTH,
    fallback: str = "component",
) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if max_length:
        slug = slug[:max_length]
    return slug or fallback
