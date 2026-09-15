from unittest.mock import patch

from app.models.instrument import Instrument
from app.services.bootstrap import BootstrapState, needs_bootstrap, run_bootstrap_sync


def _seed_one_instrument(db_session) -> None:
    db_session.add(
        Instrument(symbol="BBCA", exchange="IDX", name="Bank Central Asia Tbk", lot_size=100)
    )
    db_session.commit()


def test_needs_bootstrap_true_when_instruments_table_empty(db_session):
    assert needs_bootstrap(db_session) is True


def test_needs_bootstrap_false_when_instruments_exist(db_session):
    _seed_one_instrument(db_session)
    assert needs_bootstrap(db_session) is False


def test_bootstrap_state_snapshot_defaults_to_idle():
    state = BootstrapState()
    assert state.snapshot() == {"status": "idle", "detail": None}


def test_bootstrap_state_set_updates_snapshot():
    state = BootstrapState()
    state.set("running")
    assert state.snapshot() == {"status": "running", "detail": None}
    state.set("error", detail="no network")
    assert state.snapshot() == {"status": "error", "detail": "no network"}


def test_run_bootstrap_sync_calls_sync_and_ingest_then_marks_done():
    with (
        patch("app.services.bootstrap.SessionLocal") as mock_session_local,
        patch("app.services.bootstrap.sync_instruments") as mock_sync,
        patch("app.services.bootstrap.ingest_daily_ohlcv") as mock_ingest,
        patch("app.services.bootstrap.bootstrap_state") as mock_state,
    ):
        mock_sync.return_value = {"created": 48, "updated": 0}
        mock_ingest.return_value = {"symbols_ok": 48, "symbols_failed": 0}

        run_bootstrap_sync()

        mock_sync.assert_called_once()
        mock_ingest.assert_called_once()
        mock_state.set.assert_any_call("running")
        mock_state.set.assert_any_call("done")
        mock_session_local.return_value.close.assert_called_once()


def test_run_bootstrap_sync_marks_error_on_exception_without_raising():
    with (
        patch("app.services.bootstrap.SessionLocal") as mock_session_local,
        patch("app.services.bootstrap.sync_instruments", side_effect=RuntimeError("tidak ada internet")),
        patch("app.services.bootstrap.bootstrap_state") as mock_state,
    ):
        run_bootstrap_sync()  # tidak boleh melempar exception ke caller

        mock_state.set.assert_any_call("error", detail="tidak ada internet")
        mock_session_local.return_value.close.assert_called_once()
