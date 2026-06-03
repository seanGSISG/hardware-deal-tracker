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


def test_editable_install_has_app_package_available():
    """Regression: `uv pip install -e .` resolves setuptools `packages=["app"]`
    at build time, so the source (the `app/` dir) must be COPYed into the builder
    BEFORE the editable install line. Otherwise the build fails with
    `package directory 'app' does not exist`.
    """
    lines = [
        ln.strip()
        for ln in DOCKERFILE.read_text().splitlines()
        if not ln.strip().startswith("#") and ln.strip()
    ]
    builder_lines = lines
    # Index of the first FROM after the builder (the runtime stage), to scope the
    # check to the builder stage only.
    from_idxs = [i for i, ln in enumerate(lines) if ln.startswith("FROM ")]
    if len(from_idxs) >= 2:
        builder_lines = lines[: from_idxs[1]]

    editable_idx = next(
        (i for i, ln in enumerate(builder_lines) if "uv pip install" in ln and "-e ." in ln),
        None,
    )
    assert editable_idx is not None, "expected an editable `uv pip install -e .` line in the builder"
    copied_source_before = any(
        ln.startswith("COPY") and (". ." in ln or " app" in ln)
        for ln in builder_lines[:editable_idx]
    )
    assert copied_source_before, (
        "the app source must be COPYed before `uv pip install -e .` or the "
        "editable build fails with 'package directory app does not exist'"
    )


def test_single_uvicorn_worker():
    """The in-process APScheduler lives in the FastAPI lifespan, so running more
    than one uvicorn worker starts a scheduler per worker and fires every job
    (poll/digest/baseline/community-ingest) multiple times. Pin --workers 1.
    """
    text = DOCKERFILE.read_text()
    assert "--workers 1" in text, "uvicorn must run a single worker (in-process scheduler)"
    assert "--workers 2" not in text and "--workers 4" not in text
