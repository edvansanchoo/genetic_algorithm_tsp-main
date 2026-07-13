"""Testes do histórico de sessão LLM."""

from traveling_salesman_problem.llm.session_history import SessionHistory


def test_record_only_on_improvement():
    history = SessionHistory()
    assert history.record_if_improved(1, 100.0, 50.0, 80, 0, 3) is True
    assert history.record_if_improved(2, 110.0, 55.0, 70, 0, 3) is False
    assert history.record_if_improved(3, 90.0, 48.0, 85, 1, 3) is True
    assert len(history.all_snapshots()) == 2


def test_daily_summary_empty():
    history = SessionHistory()
    assert history.daily_summary() == {"snapshot_count": 0}


def test_weekly_summary_with_data():
    history = SessionHistory()
    history.record_if_improved(1, 100.0, 50.0, 60, 0, 2)
    history.record_if_improved(5, 80.0, 40.0, 90, 1, 2)
    summary = history.weekly_summary()
    assert summary["snapshot_count"] == 2
    assert summary["best_fitness"] == 80.0
    assert summary["worst_fitness"] == 100.0


def test_trend_tracks_generations_since_improvement():
    history = SessionHistory()
    history.record_if_improved(1, 100.0, 50.0, 80, 0, 3)
    trend = history.trend(5, 95.0)
    assert trend["geracoes_desde_melhoria"] == 4
