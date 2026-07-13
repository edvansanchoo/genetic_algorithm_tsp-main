"""Testes do buffer de logs Web."""

from traveling_salesman_problem.web.log_buffer import LogBuffer


def test_append_and_snapshot():
    buffer = LogBuffer(max_entries=3)
    buffer.append("event", "início")
    buffer.append("generation", "G1")
    snapshot = buffer.snapshot()
    assert len(snapshot) == 2
    assert snapshot[0]["type"] == "event"
    assert snapshot[1]["message"] == "G1"
    assert "ts" in snapshot[0]


def test_max_entries_trims_oldest():
    buffer = LogBuffer(max_entries=2)
    buffer.append("a", "1")
    buffer.append("b", "2")
    buffer.append("c", "3")
    snapshot = buffer.snapshot()
    assert len(snapshot) == 2
    assert snapshot[0]["message"] == "2"
    assert snapshot[1]["message"] == "3"


def test_snapshot_limit():
    buffer = LogBuffer()
    for index in range(5):
        buffer.append("t", str(index))
    limited = buffer.snapshot(limit=2)
    assert limited == buffer.snapshot()[-2:]


def test_clear():
    buffer = LogBuffer()
    buffer.append("x", "y")
    buffer.clear()
    assert buffer.snapshot() == []
