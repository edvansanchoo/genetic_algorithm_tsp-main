"""Slider para valores inteiros como quantidade de obstáculos."""

from traveling_salesman_problem.visualization.widgets.mutation_slider import MutationSlider


class IntegerSlider(MutationSlider):
    def __init__(
        self,
        position_x: int,
        position_y: int,
        width: int,
        height: int,
        value: int,
        minimum_value: int,
        maximum_value: int,
        label: str,
    ) -> None:
        super().__init__(
            position_x,
            position_y,
            width,
            height,
            float(value),
            float(minimum_value),
            float(maximum_value),
            label,
            "",
        )

    @property
    def integer_value(self) -> int:
        return int(round(self.value))
