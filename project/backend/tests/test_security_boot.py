"""story-T2.6: SECRET_KEY must fail loud on boot when left at the placeholder.

The boot guard (`validate_secret_key`) is invoked from the app lifespan so a
misconfigured deployment crashes immediately instead of silently signing JWTs
with a publicly-known key. It is a plain function so it can be unit-tested
without standing up the whole app.
"""
import pytest

from app.core.security import PLACEHOLDER_SECRET_KEY, validate_secret_key


def test_placeholder_secret_key_raises():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_secret_key(PLACEHOLDER_SECRET_KEY)


def test_empty_secret_key_raises():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_secret_key("")


def test_too_short_secret_key_raises():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_secret_key("short")


def test_strong_secret_key_passes():
    # A 32-hex-char (openssl rand -hex 32) style key is accepted.
    validate_secret_key("a" * 64)
