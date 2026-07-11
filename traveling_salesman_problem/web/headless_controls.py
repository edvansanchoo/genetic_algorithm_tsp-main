"""Controles sem Pygame para o modo Web."""

from dataclasses import dataclass


def _clamp_value(raw: float, minimum_value: float, maximum_value: float) -> float:
    return max(minimum_value, min(maximum_value, float(raw)))


@dataclass
class HeadlessSlider:
    minimum_value: float
    maximum_value: float
    label: str
    value: float = 0.0
    is_dragging: bool = False

    def __post_init__(self) -> None:
        self.value = _clamp_value(self.value, self.minimum_value, self.maximum_value)

    @property
    def integer_value(self) -> int:
        return int(round(self.value))

    def __setattr__(self, name: str, raw: object) -> None:
        if name == "value":
            minimum = getattr(self, "minimum_value", 0.0)
            maximum = getattr(self, "maximum_value", 1.0)
            object.__setattr__(
                self,
                name,
                _clamp_value(float(raw), minimum, maximum),
            )
            return
        object.__setattr__(self, name, raw)


@dataclass
class HeadlessToggle:
    label: str
    is_active: bool = False


@dataclass
class HeadlessButton:
    label: str
    subtitle: str = ""
    was_pressed: bool = False
