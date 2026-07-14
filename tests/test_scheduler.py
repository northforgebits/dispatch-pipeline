import time
from threading import Event

from apscheduler.schedulers.background import BackgroundScheduler


def test_scheduler_max_instances_prevents_overlap():
    interval_seconds = 0.05
    block_duration_seconds = 0.20
    events = []
    first_start = Event()
    second_start = Event()
    blocker = Event()

    def slow_job():
        events.append(("start", time.monotonic()))
        if first_start.is_set():
            second_start.set()
        else:
            first_start.set()
        blocker.wait(timeout=block_duration_seconds)
        events.append(("end", time.monotonic()))

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        slow_job,
        "interval",
        seconds=interval_seconds,
        max_instances=1,
    )
    scheduler.start()

    try:
        assert first_start.wait(timeout=1)
        assert second_start.wait(timeout=1)
    finally:
        scheduler.shutdown(wait=True)

    active_jobs = 0
    for event, _ in events:
        if event == "start":
            active_jobs += 1
            assert active_jobs == 1
        else:
            active_jobs -= 1

    assert active_jobs == 0

    start_times = [timestamp for event, timestamp in events if event == "start"]
    assert len(start_times) >= 2
    assert all(
        later - earlier >= block_duration_seconds
        for earlier, later in zip(start_times, start_times[1:])
    )
