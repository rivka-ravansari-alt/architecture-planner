"""Base repository with shared session access."""

from __future__ import annotations

from sqlalchemy.orm import Session


class BaseRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def commit(self) -> None:
        self._db.commit()

    def flush(self) -> None:
        self._db.flush()

    def refresh(self, instance: object) -> None:
        self._db.refresh(instance)
