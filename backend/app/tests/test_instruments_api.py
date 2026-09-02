from datetime import datetime, timezone

from app.models.instrument import Instrument
from app.models.ohlcv import OHLCV


def _seed_bbca(db_session) -> Instrument:
    instrument = Instrument(
        symbol="BBCA", exchange="IDX", name="Bank Central Asia Tbk", sector="Financials", lot_size=100
    )
    db_session.add(instrument)
    db_session.flush()

    db_session.add(
        OHLCV(
            instrument_id=instrument.id,
            timeframe="1d",
            ts=datetime(2026, 1, 2, tzinfo=timezone.utc),
            open=9200,
            high=9300,
            low=9150,
            close=9250,
            volume=1_000_000,
            value=9_250_000_000,
            frequency=1200,
        )
    )
    db_session.commit()
    return instrument


def test_list_instruments_empty(client):
    resp = client.get("/api/v1/instruments")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_instruments_search_by_symbol(client, db_session):
    _seed_bbca(db_session)

    resp = client.get("/api/v1/instruments", params={"search": "bbca"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["symbol"] == "BBCA"


def test_get_instrument_by_symbol(client, db_session):
    _seed_bbca(db_session)

    resp = client.get("/api/v1/instruments/BBCA")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Bank Central Asia Tbk"


def test_get_instrument_not_found(client):
    resp = client.get("/api/v1/instruments/NOPE")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "INSTRUMENT_NOT_FOUND"


def test_get_instrument_ohlcv_returns_stored_bars(client, db_session):
    _seed_bbca(db_session)

    resp = client.get("/api/v1/instruments/BBCA/ohlcv", params={"timeframe": "1d"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["close"] == "9250.0000"
    assert body[0]["volume"] == 1_000_000


def test_get_instrument_ohlcv_filters_by_date_range(client, db_session):
    _seed_bbca(db_session)

    resp = client.get(
        "/api/v1/instruments/BBCA/ohlcv",
        params={"timeframe": "1d", "from": "2026-06-01T00:00:00Z"},
    )
    assert resp.status_code == 200
    assert resp.json() == []
