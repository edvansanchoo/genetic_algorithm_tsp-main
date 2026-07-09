"""Controle de taxa de gerações do AG por frame."""


def compute_generations_for_frame(
    delta_seconds: float,
    generations_per_second: float,
    accumulated_seconds: float,
) -> tuple[int, float]:
    clamped_gps = max(2.0, min(5.0, generations_per_second))
    accumulated_seconds += max(0.0, delta_seconds)
    interval = 1.0 / clamped_gps
    count = 0
    while accumulated_seconds >= interval:
        count += 1
        accumulated_seconds -= interval
    return count, accumulated_seconds
