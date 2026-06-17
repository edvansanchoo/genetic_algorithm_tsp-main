"""Slider contínuo para valores como taxa de mutação."""

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.visualization.application_layout import draw_card
from traveling_salesman_problem.visualization.fonts import get_monospace_font, get_user_interface_font


class MutationSlider:
    TRACK_VERTICAL_OFFSET = 34

    def __init__(
        self,
        position_x: int,
        position_y: int,
        width: int,
        height: int,
        value: float = 0.5,
        minimum_value: float = 0.0,
        maximum_value: float = 1.0,
        label: str = "Valor",
        value_suffix: str = "",
    ) -> None:
        self.rectangle = pygame.Rect(position_x, position_y, width, height)
        self.track_rectangle = pygame.Rect(
            position_x + 12,
            position_y + self.TRACK_VERTICAL_OFFSET,
            width - 24,
            8,
        )
        self.minimum_value = minimum_value
        self.maximum_value = maximum_value
        self.value = value
        self.label = label
        self.value_suffix = value_suffix
        self.is_dragging = False

    def _value_from_mouse_x(self, mouse_x: int) -> float:
        relative_position = (mouse_x - self.track_rectangle.left) / self.track_rectangle.width
        relative_position = max(0.0, min(1.0, relative_position))
        return self.minimum_value + relative_position * (
            self.maximum_value - self.minimum_value
        )

    def _knob_center_x(self) -> int:
        value_span = self.maximum_value - self.minimum_value
        relative_position = (
            0 if value_span == 0 else (self.value - self.minimum_value) / value_span
        )
        return self.track_rectangle.left + int(relative_position * self.track_rectangle.width)

    def _formatted_value(self) -> str:
        if self.value_suffix == "%":
            return f"{self.value * 100:.0f}{self.value_suffix}"
        return f"{int(round(self.value))}{self.value_suffix}"

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rectangle.collidepoint(event.pos):
                self.is_dragging = True
                self.value = self._value_from_mouse_x(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            self.value = self._value_from_mouse_x(event.pos[0])

    def draw(self, screen: pygame.Surface) -> None:
        draw_card(screen, self.rectangle)
        label_font = get_user_interface_font(13)
        value_font = get_monospace_font(13)
        screen.blit(
            label_font.render(self.label, True, VisualTheme.text_primary),
            (self.rectangle.x + 12, self.rectangle.y + 8),
        )
        value_surface = value_font.render(self._formatted_value(), True, VisualTheme.accent)
        value_rectangle = value_surface.get_rect(
            topright=(self.rectangle.right - 12, self.rectangle.y + 8),
        )
        screen.blit(value_surface, value_rectangle)

        pygame.draw.rect(
            screen,
            VisualTheme.neutral_background,
            self.track_rectangle,
            border_radius=4,
        )
        filled_width = max(0, self._knob_center_x() - self.track_rectangle.left)
        if filled_width > 0:
            pygame.draw.rect(
                screen,
                VisualTheme.accent_track,
                pygame.Rect(
                    self.track_rectangle.x,
                    self.track_rectangle.y,
                    filled_width,
                    self.track_rectangle.height,
                ),
                border_radius=4,
            )
        knob_x = self._knob_center_x()
        pygame.draw.circle(
            screen,
            VisualTheme.accent,
            (knob_x, self.track_rectangle.centery),
            7,
        )
        pygame.draw.circle(
            screen,
            VisualTheme.text_inverse,
            (knob_x, self.track_rectangle.centery),
            7,
            width=2,
        )
