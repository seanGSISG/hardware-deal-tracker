"""Tests for the direct-bcrypt password hashing (migrated off passlib).

Covers: round-trip verify, backward-compat with passlib-emitted $2b$ hashes,
needs_rehash on stale cost / non-bcrypt legacy hashes, and 72-byte truncation.
"""
import bcrypt
import pytest

from app.core.security import (
    BCRYPT_ROUNDS,
    get_password_hash,
    needs_rehash,
    verify_password,
)

# A standard $2b$ bcrypt hash at cost 12 — byte-for-byte what passlib's
# CryptContext(schemes=["bcrypt"]) emitted. Proves legacy stored hashes still verify.
LEGACY_PASSLIB_HASH = "$2b$12$RZnL3ggI.RNajq1u9YIgDe4KCS.oqbpZ2ZL2PiolsAyK9Vbr97/Be"
LEGACY_PLAINTEXT = "correct horse battery staple"


def test_round_trip():
    pw = "s3cret-passphrase"
    hashed = get_password_hash(pw)
    assert verify_password(pw, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_hash_is_standard_bcrypt():
    hashed = get_password_hash("anything")
    assert hashed.startswith(("$2b$", "$2a$", "$2y$"))


def test_backward_compat_with_passlib_hash():
    # An existing passlib-produced $2b$ hash must still verify under the new code.
    assert verify_password(LEGACY_PLAINTEXT, LEGACY_PASSLIB_HASH) is True
    assert verify_password("nope", LEGACY_PASSLIB_HASH) is False


def test_needs_rehash_stale_cost():
    # A bcrypt hash at a LOWER cost than the current target should need rehash.
    weak = bcrypt.hashpw(b"pw", bcrypt.gensalt(BCRYPT_ROUNDS - 2)).decode()
    assert needs_rehash(weak) is True


def test_needs_rehash_current_cost_false():
    current = get_password_hash("pw")
    assert needs_rehash(current) is False


def test_needs_rehash_non_bcrypt_legacy():
    # A non-bcrypt legacy format (e.g. sha256_crypt or junk) must need rehash.
    assert needs_rehash("$5$rounds=535000$abc$def") is True
    assert needs_rehash("not-a-hash-at-all") is True


def test_long_password_over_72_bytes_does_not_raise():
    long_pw = "a" * 100  # > 72 bytes
    hashed = get_password_hash(long_pw)
    assert verify_password(long_pw, hashed) is True


def test_72_byte_truncation_is_deliberate():
    # bcrypt truncates at 72 bytes; two passwords sharing the first 72 bytes verify
    # interchangeably. We assert that truncation is happening (documented behavior),
    # not raising.
    base = "x" * 72
    hashed = get_password_hash(base)
    assert verify_password(base + "EXTRA", hashed) is True


@pytest.mark.asyncio
async def test_verify_password_malformed_hash_returns_false():
    # A malformed stored hash must return False, not raise.
    assert verify_password("pw", "") is False
    assert verify_password("pw", "garbage") is False


@pytest.mark.asyncio
async def test_login_rehashes_stale_hash(unauth_client, db):
    """Logging in with a stale (low-cost) stored hash transparently upgrades it."""
    from sqlalchemy import select

    from app.models.user import User

    plaintext = "login-password"
    stale_hash = bcrypt.hashpw(
        plaintext.encode("utf-8"), bcrypt.gensalt(BCRYPT_ROUNDS - 2)
    ).decode()
    user = User(
        username="rehashme",
        email="rehashme@example.com",
        hashed_password=stale_hash,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    resp = await unauth_client.post(
        "/api/v1/auth/login", json={"username": "rehashme", "password": plaintext}
    )
    assert resp.status_code == 200, resp.text

    refreshed = (
        await db.execute(select(User).where(User.username == "rehashme"))
    ).scalar_one()
    assert refreshed.hashed_password != stale_hash
    assert needs_rehash(refreshed.hashed_password) is False
    assert verify_password(plaintext, refreshed.hashed_password) is True


@pytest.mark.asyncio
async def test_login_does_not_rehash_current_hash(unauth_client, db):
    """A login against an already-current hash leaves the stored hash unchanged."""
    from sqlalchemy import select

    from app.models.user import User

    plaintext = "fresh-password"
    current_hash = get_password_hash(plaintext)
    user = User(
        username="freshuser",
        email="freshuser@example.com",
        hashed_password=current_hash,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    resp = await unauth_client.post(
        "/api/v1/auth/login", json={"username": "freshuser", "password": plaintext}
    )
    assert resp.status_code == 200, resp.text

    refreshed = (
        await db.execute(select(User).where(User.username == "freshuser"))
    ).scalar_one()
    assert refreshed.hashed_password == current_hash
