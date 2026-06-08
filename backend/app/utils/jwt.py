"""JWT token creation and validation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config.params import JWT_ALGORITHM
from app.config.settings import settings


class JwtService:
    def create_access_token(self, user_id: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
        payload = {"sub": user_id, "exp": expire}
        return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)

    def decode_access_token(self, token: str) -> str | None:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
        except JWTError:
            return None
        sub = payload.get("sub")
        return sub if isinstance(sub, str) else None
