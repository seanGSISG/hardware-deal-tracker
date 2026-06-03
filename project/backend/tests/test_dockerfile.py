"""T3.7 — the runtime image must not ship dev/test tooling.

The previous Dockerfile installed `.[dev]` and copied the whole site-packages tree
into the runtime stage, baking pytest/ruff/etc into the production image. We assert
the install line drops the [dev] extra and keeps a multi-stage build.
"""
from pathlib import Path

DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"


def _install_lines() -> list[str]:
    return [
        line.strip()
        for line in DOCKERFILE.read_text().splitlines()
        if "uv pip install" in line and not line.strip().startswith("#")
    ]


def test_dockerfile_exists_and_multistage():
    text = DOCKERFILE.read_text()
    assert "AS builder" in text
    # A second FROM (the runtime stage) keeps the image slim.
    assert text.count("FROM ") >= 2


def test_no_dev_extra_in_pip_install():
    installs = _install_lines()
    assert installs, "expected at least one uv pip install line"
    for line in installs:
        assert "[dev]" not in line, f"dev deps leak into the image: {line}"
        assert ".[dev]" not in line
