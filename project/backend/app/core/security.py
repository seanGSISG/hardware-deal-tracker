from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# Direct bcrypt (passlib is unmaintained and breaks on bcrypt>=4). Existing
# passlib-emitted hashes are standard $2b$ bcrypt strings, so they keep verifying.
BCRYPT_ROUNDS = 12
_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")
# bcrypt only consumes the first 72 BYTES of the password and historically raised
# on longer inputs; we truncate deliberately and consistently so long passphrases
# hash without error (the truncation is part of bcrypt's design).
_BCRYPT_MAX_BYTES = 72


def _to_bcrypt_bytes(password: str) -> bytes:
    """UTF-8 encode and truncate to bcrypt's 72-byte limit (deliberate)."""
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]

# Name of the httpOnly session cookie that carries the JWT (ADR-002 / feature-002).
# Defined here (a leaf module with no app-layer imports) so both the auth endpoint
# and the deps resolver can share it without a circular import.
SESSION_COOKIE_NAME = "session"

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
    """Verify a plaintext against a stored bcrypt hash.

    Returns False (never raises) for malformed or non-bcrypt stored hashes, so a
    legacy/garbage row simply fails authentication instead of crashing the request.
    """
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(_to_bcrypt_bytes(plain_password), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    """Produce a standard $2b$ bcrypt hash at the current cost factor."""
    return bcrypt.hashpw(_to_bcrypt_bytes(password), bcrypt.gensalt(BCRYPT_ROUNDS)).decode("utf-8")


def needs_rehash(hashed_password: str) -> bool:
    """True if a stored hash should be replaced on next successful login.

    Triggers a rehash when the hash is not a bcrypt hash at all (a non-bcrypt legacy
    format) or when its embedded cost factor is below the current BCRYPT_ROUNDS.
    """
    if not hashed_password or not hashed_password.startswith(_BCRYPT_PREFIXES):
        return True
    # bcrypt layout: $2b$<cost>$<22-char-salt><31-char-hash>
    try:
        cost = int(hashed_password.split("$")[2])
    except (IndexError, ValueError):
        return True
    return cost < BCRYPT_ROUNDS


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
