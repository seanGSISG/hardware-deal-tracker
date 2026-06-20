# Build the backend image reproducibly from uv.lock

**Area:** build / CI
**Status:** idea
**Filed:** 2026-06-20

## Problem

`backend/Dockerfile` installs deps with `uv pip install --system --no-cache -e .`,
which resolves against the **`>=` constraints in `pyproject.toml` and ignores
`uv.lock`**. Every rebuild therefore pulls the newest compatible versions, so the
image is not reproducible. On 2026-06-20 a routine rebuild pulled `fastapi 0.138.0`
(lock pins `0.136.3`); its `_IncludedRouter` router wrapper is unintrospectable by
`prometheus-fastapi-instrumentator 8.0.0`, which 500'd on every request. Worked
around by capping `fastapi<0.137` (commit `a0bde04`), but the same class of drift
can recur for any other transitive dep (starlette, pydantic, etc.).

## Desired end state

Image builds pin to `uv.lock` so two builds of the same commit are byte-identical
on deps. Candidate approaches (need to pick one + verify the multi-stage COPY paths
still work):

- `uv export --frozen --no-dev --no-emit-project -o requirements.lock.txt` then
  `uv pip install --system --no-cache -r requirements.lock.txt` + `-e . --no-deps`.
- `uv sync --frozen --no-dev` into a `.venv` and adjust the runtime-stage COPY
  from `.venv` instead of system site-packages.

## Open questions

- Does `uv export` flag set match the installed uv version in the build image?
- Keep the editable `-e .` install, or switch to a regular install of the app pkg?
- Add a CI check that rebuilds and hits `/api/v1/health` so dep drift fails the
  pipeline instead of production.

## Trigger to revisit

Next time the backend image is rebuilt for any reason, or before the MVP4 work —
fold this in so the rebuild is safe.
