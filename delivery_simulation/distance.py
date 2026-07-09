"""Cálculo de distância euclidiana."""

import math

from delivery_simulation.models import Coordinate


def euclidean(point_a: Coordinate, point_b: Coordinate) -> float:
    delta_x = point_b[0] - point_a[0]
    delta_y = point_b[1] - point_a[1]
    return math.hypot(delta_x, delta_y)
