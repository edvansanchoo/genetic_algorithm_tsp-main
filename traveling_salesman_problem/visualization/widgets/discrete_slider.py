"""Slider com valores discretos pré-definidos."""

from typing import Tuple

import pygame

from traveling_salesman_problem.visualization.widgets.mutation_slider import MutationSlider


class DiscreteSlider(MutationSlider):
    def __init__(
        self,
        position_x: int,
        position_y: int,
        width: int,
        height: int,
        value: int,
        allowed_values: Tuple[int, ...],
        label: str,
    ) -> None:
        if not allowed_values:
            raise ValueError("allowed_values não pode ser vazio")
        self.allowed_values = allowed_values
        minimum = float(min(allowed_values))
        maximum = float(max(allowed_values))
        super().__init__(
            position_x,
            position_y,
            width,
            height,
            float(value),
            minimum,
            maximum,
            label,
            "",
        )
        self.snap_to_nearest()

    def snap_to_nearest(self) -> None:
        nearest = min(self.allowed_values, key=lambda item: abs(item - self.value))
        self.value = float(nearest)

    @property
    def selected_value(self) -> int:
        return int(self.value)

    def handle_event(self, event) -> None:
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONUP:
            self.snap_to_nearest()
