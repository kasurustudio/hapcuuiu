from app.models.instrument import Instrument


def test_system_status_reports_postgres_and_empty_instruments(client):
    resp = client.get("/api/v1/system/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["database"] == "postgres"
    assert body["instrument_count"] == 0
    assert body["bootstrap"] == {"status": "idle", "detail": None}


def test_system_status_reflects_instrument_count(client, db_session):
    db_session.add(Instrument(symbol="BBCA", exchange="IDX", name="BCA", lot_size=100))
    db_session.commit()

    resp = client.get("/api/v1/system/status")
    assert resp.json()["instrument_count"] == 1
