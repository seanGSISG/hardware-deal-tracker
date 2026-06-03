from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# The insecure default shipped in config.py / docker-compose. If the running app
# still carries this value (or anything too weak) we refuse to boot rather than
# sign JWTs with a publicly-known key.
PLACEHOLDER_SECRET_KEY = "change-me-in-production-min-32-chars"
MIN_SECRET_KEY_LENGTH = 32


def validate_secret_key(secret_key: str | None = None) -> None:
    """Fail loud (RuntimeError) if SECRET_KEY is unset, the placeholder, or weak.

    Called from the app lifespan (boot) so a misconfigured deployment crashes
    immediately. Defaults to the configured value when no argument is given.
    """
    key = settings.SECRET_KEY if secret_key is None else secret_key
    if not key or key == PLACEHOLDER_SECRET_KEY or len(key) < MIN_SECRET_KEY_LENGTH:
        raise RuntimeError(
            "SECRET_KEY is unset, still the insecure placeholder, or shorter than "
            f"{MIN_SECRET_KEY_LENGTH} chars. Generate a strong key with "
            "`openssl rand -hex 32` and set SECRET_KEY before starting the app."
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
