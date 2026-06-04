"""User persistence."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def find_by_google_sub(self, google_sub: str) -> User | None:
        return self._db.query(User).filter(User.google_sub == google_sub).one_or_none()

    def find_by_id(self, user_id: str) -> User | None:
        return self._db.get(User, user_id)

    def create(self, *, google_sub: str, email: str, name: str, picture: str | None) -> User:
        now = datetime.now(timezone.utc)
        user = User(
            google_sub=google_sub,
            email=email,
            name=name,
            picture=picture,
            last_login_at=now,
        )
        self._db.add(user)
        return user

    def update_profile(
        self,
        user: User,
        *,
        email: str,
        name: str,
        picture: str | None,
    ) -> User:
        now = datetime.now(timezone.utc)
        user.email = email
        user.name = name
        user.picture = picture
        user.last_login_at = now
        return user
