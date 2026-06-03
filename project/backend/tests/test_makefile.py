"""T3.8 — `make up` must build images before starting containers.

Stale images are a common foot-gun: editing source then `make up` would silently run
the old build. We assert the `up` target's recipe runs `docker compose build` ahead of
`docker compose up`.
"""
import re
from pathlib import Path

MAKEFILE = Path(__file__).resolve().parents[2] / "Makefile"


def _up_recipe() -> list[str]:
    lines = MAKEFILE.read_text().splitlines()
    recipe: list[str] = []
    in_target = False
    for line in lines:
        if re.match(r"^up:", line):
            in_target = True
            continue
        if in_target:
            if line.startswith("\t"):
                recipe.append(line.strip())
            elif line.strip() == "":
                continue
            else:
                break
    return recipe


def test_up_builds_before_starting():
    recipe = _up_recipe()
    assert recipe, "up target has no recipe"
    joined = "\n".join(recipe)
    assert "docker compose build" in joined
    assert "docker compose up" in joined
    # build must come before up
    assert joined.index("docker compose build") < joined.index("docker compose up")
