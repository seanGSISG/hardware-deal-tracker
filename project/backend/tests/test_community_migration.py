"""feature-007 story-5: migration chains correctly off the current head.

Proves the community_signal_leads migration sets down_revision='item_price_baselines'
and that the migration graph still has exactly ONE linear head (no fork).
"""
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

_BACKEND = Path(__file__).resolve().parents[1]


def _scripts() -> ScriptDirectory:
    cfg = Config(str(_BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND / "alembic"))
    return ScriptDirectory.from_config(cfg)


def test_single_linear_head():
    assert list(_scripts().get_heads()) == ["community_signal_leads"]


def test_down_revision_is_item_price_baselines():
    rev = _scripts().get_revision("community_signal_leads")
    assert rev.down_revision == "item_price_baselines"
