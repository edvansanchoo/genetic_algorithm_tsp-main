"""Testes dos controles headless (modo Web)."""

from traveling_salesman_problem.web.headless_controls import (
    HeadlessButton,
    HeadlessSlider,
    HeadlessToggle,
)


def test_slider_clamps_value():
    slider = HeadlessSlider(0, 10, "test", value=15)
    assert slider.value == 10
    slider.value = -5
    assert slider.value == 0


def test_slider_integer_value():
    slider = HeadlessSlider(0, 10, "test", value=4.6)
    assert slider.integer_value == 5


def test_toggle_defaults():
    toggle = HeadlessToggle("mesh")
    assert toggle.is_active is False
    toggle.is_active = True
    assert toggle.is_active is True


def test_button_defaults():
    button = HeadlessButton("Reiniciar", subtitle="GA")
    assert button.was_pressed is False
