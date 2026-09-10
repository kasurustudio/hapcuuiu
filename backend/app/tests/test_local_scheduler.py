from app.workers.local_scheduler import start_local_scheduler, stop_local_scheduler


def test_start_local_scheduler_registers_expected_jobs():
    scheduler = start_local_scheduler()
    try:
        job_ids = {job.id for job in scheduler.get_jobs()}
        assert job_ids == {"sync_instruments", "ingest_daily_ohlcv"}
    finally:
        stop_local_scheduler()


def test_start_local_scheduler_is_idempotent():
    scheduler1 = start_local_scheduler()
    scheduler2 = start_local_scheduler()
    try:
        assert scheduler1 is scheduler2
        assert len(scheduler1.get_jobs()) == 2
    finally:
        stop_local_scheduler()


def test_stop_local_scheduler_allows_restart():
    start_local_scheduler()
    stop_local_scheduler()
    scheduler = start_local_scheduler()
    try:
        assert len(scheduler.get_jobs()) == 2
    finally:
        stop_local_scheduler()


def test_sync_instruments_job_scheduled_daily_at_0600_wib():
    scheduler = start_local_scheduler()
    try:
        job = scheduler.get_job("sync_instruments")
        trigger_str = str(job.trigger)
        assert "hour='6'" in trigger_str
        assert "minute='0'" in trigger_str
    finally:
        stop_local_scheduler()


def test_ingest_ohlcv_job_scheduled_weekdays_at_1730_wib():
    scheduler = start_local_scheduler()
    try:
        job = scheduler.get_job("ingest_daily_ohlcv")
        trigger_str = str(job.trigger)
        assert "hour='17'" in trigger_str
        assert "minute='30'" in trigger_str
        assert "day_of_week='mon-fri'" in trigger_str
    finally:
        stop_local_scheduler()
