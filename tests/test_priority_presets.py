"""Testes do preset hospitalar de prioridades."""

from traveling_salesman_problem.problem.priority_presets import (
    HOSPITAL_PRESET_SEED,
    apply_hospital_priority_preset,
)


def test_hospital_preset_is_deterministic():
    first = apply_hospital_priority_preset(20)
    second = apply_hospital_priority_preset(20)
    assert first == second


def test_hospital_preset_has_critical_deliveries():
    priorities = apply_hospital_priority_preset(10)
    critical = sum(1 for value in priorities if value >= 8)
    assert critical >= 1
    assert all(1 <= value <= 10 for value in priorities)


def test_hospital_preset_seed_constant():
    assert HOSPITAL_PRESET_SEED == 42
