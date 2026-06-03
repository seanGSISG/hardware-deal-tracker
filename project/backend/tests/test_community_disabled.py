"""feature-007 story-7: app-works-when-disabled guarantee.

With ENABLE_COMMUNITY_SIGNAL=False (the default) the feature is fully dormant:
the flag defaults off, the scheduler registers NO community ingest job, the
ingest entrypoint does zero network/AI work and returns [], and the endpoint
reports a disabled/empty response. Importing the feature modules causes no
behavior change.
"""
from app.core.config import settings
from app.services.community.source import CommunitySignalSource


def test_flag_defaults_off():
    # The shipped default must be off so the app behaves byte-for-byte unchanged.
    assert settings.ENABLE_COMMUNITY_SIGNAL is False


async def test_ingest_noop_when_disabled(db, monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_COMMUNITY_SIGNAL", False)

    import app.services.community.source as source_mod

    def _boom(*a, **k):  # pragma: no cover
        raise AssertionError("no network/AI allowed when disabled")

    monkeypatch.setattr(source_mod, "RedditClient", lambda *a, **k: _boom())
    leads = await CommunitySignalSource().ingest(db)
    assert leads == []


async def test_scheduler_registers_no_community_job_when_disabled(monkeypatch):
    # Build the app's scheduler the same way main.lifespan does and assert that
    # with the gate off there is no community_ingest_tick job.
    monkeypatch.setattr(settings, "ENABLE_COMMUNITY_SIGNAL", False)
    monkeypatch.setattr(settings, "SCHEDULER_ENABLED", True)
    monkeypatch.setattr(settings, "SECRET_KEY", "x" * 48)
    from app.main import app, lifespan

    async with lifespan(app):
        scheduler = app.state.scheduler
        assert scheduler is not None
        job_ids = {job.id for job in scheduler.get_jobs()}
        assert "community_ingest_tick" not in job_ids


async def test_scheduler_registers_community_job_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_COMMUNITY_SIGNAL", True)
    monkeypatch.setattr(settings, "SCHEDULER_ENABLED", True)
    monkeypatch.setattr(settings, "SECRET_KEY", "x" * 48)
    from app.main import app, lifespan

    async with lifespan(app):
        scheduler = app.state.scheduler
        job_ids = {job.id for job in scheduler.get_jobs()}
        assert "community_ingest_tick" in job_ids
