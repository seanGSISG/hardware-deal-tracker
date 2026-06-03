from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import TokenData, UserLogin, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])

# Name of the httpOnly session cookie that carries the JWT (ADR-002 / feature-002).
SESSION_COOKIE_NAME = "session"


def _set_session_cookie(response: Response, token: str) -> None:
    """Attach the JWT to an httpOnly + Secure + SameSite=Lax cookie.

    max-age is derived from the configured JWT TTL (ACCESS_TOKEN_EXPIRE_MINUTES)
    so the cookie and the token expire together. SameSite=Lax keeps cross-subdomain
    navigation within *.lab.lsdmt.me working while still blocking CSRF on POSTs.
    """
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    """Clear the session cookie (logout). Attributes must match the set call."""
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=True,
        samesite="lax",
    )


@router.post("/register", response_model=TokenData)
async def register(
    data: UserRegister, response: Response, db: AsyncSession = Depends(get_db)
):
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-service registration is disabled.",
        )
    result = await db.execute(
        select(User).where((User.username == data.username) | (User.email == data.email))
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or email already exists")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password)
    )
    db.add(user)
    await db.flush()
    token = create_access_token({"sub": str(user.id)})
    # Issue the session cookie on register too, so the just-registered user is
    # immediately authenticated server-side (mirrors login).
    _set_session_cookie(response, token)
    return TokenData(access_token=token)


@router.post("/login", response_model=TokenData)
async def login(
    data: UserLogin, response: Response, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    # Set the httpOnly session cookie AND return the bearer token body so API
    # clients / the pytest bearer fixtures are unaffected.
    _set_session_cookie(response, token)
    return TokenData(access_token=token)


@router.post("/logout")
async def logout(response: Response):
    """Clear the session cookie. Bearer clients simply drop their token."""
    _clear_session_cookie(response)
    return {"detail": "logged out"}
