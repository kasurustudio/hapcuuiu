from datetime import datetime, timedelta, timezone

import numpy as np

from app.models.instrument import Instrument
from app.models.ohlcv import OHLCV


def _seed_instrument_with_bars(db_session, n: int = 260, symbol: str = "BBCA") -> Instrument:
    instrument = Instrument(symbol=symbol, exchange="IDX", name="Bank Central Asia Tbk", sector="Financials")
    db_session.add(instrument)
    db_session.flush()

    rng = np.random.default_rng(42)
    close = 9000 + np.cumsum(rng.normal(5, 50, n))
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)

    for i in range(n):
        c = float(close[i])
        h = c + float(rng.uniform(10, 50))
        l = c - float(rng.uniform(10, 50))
        o = c + float(rng.uniform(-20, 20))
        db_session.add(
            OHLCV(
                instrument_id=instrument.id,
                timeframe="1d",
                ts=start + timedelta(days=i),
                open=round(o, 4),
                high=round(h, 4),
                low=round(l, 4),
                close=round(c, 4),
                volume=int(rng.integers(100000, 5000000)),
            )
        )
    db_session.commit()
    return instrument


def test_indicators_endpoint_returns_snapshot(client, db_session):
    _seed_instrument_with_bars(db_session)

    resp = client.get("/api/v1/instruments/BBCA/indicators", params={"timeframe": "1d"})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"trend", "momentum", "volatility", "volume", "structure"}
    assert body["trend"]["sma20"] is not None
    assert 0 <= body["momentum"]["rsi14"] <= 100


def test_indicators_endpoint_insufficient_data_returns_422(client, db_session):
    _seed_instrument_with_bars(db_session, n=10)

    resp = client.get("/api/v1/instruments/BBCA/indicators", params={"timeframe": "1d"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "INSUFFICIENT_DATA"


def test_indicators_endpoint_404_for_unknown_symbol(client):
    resp = client.get("/api/v1/instruments/NOPE/indicators")
    assert resp.status_code == 404


def test_levels_endpoint_returns_support_and_resistance(client, db_session):
    _seed_instrument_with_bars(db_session)

    resp = client.get("/api/v1/instruments/BBCA/levels", params={"timeframe": "1d"})
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    if body:
        assert body[0]["level_type"] in ("support", "resistance")
        assert "strength" in body[0]
        assert "role_flipped" in body[0]


def test_patterns_endpoint_returns_list_with_valid_shape(client, db_session):
    _seed_instrument_with_bars(db_session)

    resp = client.get("/api/v1/instruments/BBCA/patterns", params={"timeframe": "1d"})
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    for pattern in body:
        assert pattern["direction"] in ("bullish", "bearish", "neutral")
        assert pattern["reliability_score"] > 0
        assert "ts" in pattern


def test_levels_and_patterns_share_insufficient_data_gate(client, db_session):
    _seed_instrument_with_bars(db_session, n=5)

    levels_resp = client.get("/api/v1/instruments/BBCA/levels")
    patterns_resp = client.get("/api/v1/instruments/BBCA/patterns")

    assert levels_resp.status_code == 422
    assert patterns_resp.status_code == 422
