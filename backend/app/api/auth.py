from __future__ import annotations

import logging
from datetime import datetime, timezone

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth.deps import get_current_user
from ..auth.jwt import create_access_token
from ..config import settings
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def _session_cookie(token: str) -> dict:
    return {
        "key": settings.session_cookie_name,
        "value": token,
        "httponly": True,
        "secure": settings.session_cookie_secure,
        "samesite": "lax",
        "path": "/",
        "max_age": settings.jwt_expire_minutes * 60,
    }


def _clear_session_cookie() -> dict:
    return {
        "key": settings.session_cookie_name,
        "value": "",
        "httponly": True,
        "secure": settings.session_cookie_secure,
        "samesite": "lax",
        "path": "/",
        "max_age": 0,
    }


@router.get("/google")
async def google_login(request: Request):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured",
        )
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured",
        )

    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        logger.exception("Google OAuth callback failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to complete Google sign-in: {exc}",
        ) from exc

    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = await oauth.google.userinfo(token=token)

    google_sub = userinfo.get("sub")
    if not google_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account id missing",
        )

    email = userinfo.get("email") or ""
    name = userinfo.get("name") or ""
    picture = userinfo.get("picture")

    user = db.query(models.User).filter(models.User.google_sub == google_sub).one_or_none()
    now = datetime.now(timezone.utc)
    if user is None:
        user = models.User(
            google_sub=google_sub,
            email=email,
            name=name,
            picture=picture,
            last_login_at=now,
        )
        db.add(user)
    else:
        user.email = email
        user.name = name
        user.picture = picture
        user.last_login_at = now
    db.commit()
    db.refresh(user)

    session_token = create_access_token(user.id)
    response = RedirectResponse(url=settings.frontend_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(**_session_cookie(session_token))
    return response


@router.get("/me", response_model=schemas.UserOut)
def auth_me(user: models.User = Depends(get_current_user)) -> models.User:
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    from starlette.responses import Response

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.set_cookie(**_clear_session_cookie())
    return response
