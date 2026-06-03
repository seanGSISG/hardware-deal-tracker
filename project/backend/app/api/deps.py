from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import SESSION_COOKIE_NAME, verify_token
from app.db.session import session_factory
from app.models.user import User

# auto_error=False so a MISSING Authorization header does not 401/403 on its own:
# the session cookie is an equally valid auth source (ADR-002 / feature-002). We
# raise 401 ourselves only when neither source yields a valid JWT.
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    # Resolve the JWT from EITHER the Authorization: Bearer header OR the session
    # cookie. The bearer header is tried first (API clients / pytest fixtures);
    # the httpOnly cookie is the browser path. 401 only when NEITHER is valid.
    token = None
    if credentials is not None:
        token = verify_token(credentials.credentials)
    if not token:
        cookie_value = request.cookies.get(SESSION_COOKIE_NAME)
        if cookie_value:
            token = verify_token(cookie_value)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = token.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """Require the authenticated user to be an admin.

    Used to gate user-managed catalog mutations (create/update/delete tracked
    items). Reads stay open to any authenticated user via get_current_user.
    """
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user
