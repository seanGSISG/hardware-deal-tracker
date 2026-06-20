"""feature-007 story-5: migration chains correctly off the current head.

Proves the community_signal_leads migration chains onto the prior head and that
the migration graph still has exactly ONE linear head (no fork). At mega-plan
merge time the prior head became 'semantic_embeddings' (feature-006), so the
down_revision was re-threaded from 'item_price_baselines' to keep one linear head.
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
    # The graph must stay a single linear head (no fork). The head advances as new
    # migrations chain on; cascade_delete_tracked_items (2026-06-20) is the current
    # tip, chained off community_signal_leads.
    assert list(_scripts().get_heads()) == ["cascade_delete_tracked_items"]


def test_down_revision_chains_onto_prior_head():
    rev = _scripts().get_revision("community_signal_leads")
    # Re-threaded onto feature-006's migration at merge time for a single head.
    assert rev.down_revision == "semantic_embeddings"
