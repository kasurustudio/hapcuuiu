from app.models.instrument import Instrument
from app.services.ingest import sync_instruments as _sync_instruments
from app.services.market_data.lq45_seed import LQ45_SEED


def test_sync_instruments_creates_all_seed_symbols(db_session):
    result = _sync_instruments(db_session)

    assert result["created"] == len(LQ45_SEED)
    assert result["updated"] == 0

    count = db_session.query(Instrument).filter(Instrument.exchange == "IDX").count()
    assert count == len(LQ45_SEED)


def test_sync_instruments_is_idempotent(db_session):
    _sync_instruments(db_session)
    result_second_run = _sync_instruments(db_session)

    assert result_second_run["created"] == 0
    assert result_second_run["updated"] == len(LQ45_SEED)

    count = db_session.query(Instrument).filter(Instrument.exchange == "IDX").count()
    assert count == len(LQ45_SEED)


def test_sync_instruments_sets_default_lot_size(db_session):
    _sync_instruments(db_session)
    bbca = (
        db_session.query(Instrument)
        .filter(Instrument.symbol == "BBCA", Instrument.exchange == "IDX")
        .one()
    )
    assert bbca.lot_size == 100
    assert bbca.is_active is True
