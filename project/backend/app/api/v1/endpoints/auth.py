from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, needs_rehash, verify_password
from app.models.user import User
from app.schemas.auth import TokenData, UserLogin, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenData)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
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
    return TokenData(access_token=token)


@router.post("/login", response_model=TokenData)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Transparent rehash-on-login: if the stored hash is stale (legacy format or a
    # lower bcrypt cost than the current target), re-hash the supplied plaintext and
    # persist the upgrade so the hash silently modernizes on the user's next login.
    if needs_rehash(user.hashed_password):
        user.hashed_password = get_password_hash(data.password)
        await db.flush()
    token = create_access_token({"sub": str(user.id)})
    return TokenData(access_token=token)
