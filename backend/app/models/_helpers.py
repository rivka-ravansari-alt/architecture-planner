from __future__ import annotations

import uuid
from datetime import datetime, timezone


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)
