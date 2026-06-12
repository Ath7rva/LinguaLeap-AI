from app.services.spaced_repetition import schedule_sm2


def test_successful_recall_increases_interval():
    first = schedule_sm2(0, 1, 2.5, 5)
    second = schedule_sm2(first["repetition"], first["interval_days"], first["difficulty"], 5)
    third = schedule_sm2(second["repetition"], second["interval_days"], second["difficulty"], 5)
    assert first["interval_days"] == 1
    assert second["interval_days"] == 6
    assert third["interval_days"] > second["interval_days"]


def test_failed_recall_resets_schedule():
    result = schedule_sm2(4, 30, 2.5, 1)
    assert result["repetition"] == 0
    assert result["interval_days"] == 1
