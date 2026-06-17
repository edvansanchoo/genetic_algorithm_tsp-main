"""Interruptor Ativo/Inativo para opções da interface."""

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.visualization.application_layout import draw_card
from traveling_salesman_problem.visualization.fonts import get_user_interface_font


def _mouse_over_rectangle(rectangle: pygame.Rect) -> bool:
    return rectangle.collidepoint(pygame.mouse.get_pos())


class ToggleButton:
    PILL_WIDTH = 68
    PILL_HEIGHT = 22

    def __init__(
        self,
        position_x: int,
        position_y: int,
        width: int,
        height: int,
        label: str,
        is_active: bool = True,
    ) -> None:
        self.rectangle = pygame.Rect(position_x, position_y, width, height)
        self.label = label
        self.is_active = is_active

    @property
    def pill_rectangle(self) -> pygame.Rect:
        return pygame.Rect(
            self.rectangle.right - 12 - self.PILL_WIDTH,
            self.rectangle.centery - self.PILL_HEIGHT // 2,
            self.PILL_WIDTH,
            self.PILL_HEIGHT,
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rectangle.collidepoint(event.pos):
                self.is_active = not self.is_active
                return True
        return False

    def draw(self, screen: pygame.Surface) -> None:
        is_hovered = _mouse_over_rectangle(self.rectangle)
        draw_card(screen, self.rectangle)
        if is_hovered:
            pygame.draw.rect(
                screen,
                VisualTheme.accent,
                self.rectangle,
                width=1,
                border_radius=8,
            )

        screen.blit(
            get_user_interface_font(13).render(self.label, True, VisualTheme.text_primary),
            (self.rectangle.x + 12, self.rectangle.centery - 8),
        )

        pill = self.pill_rectangle
        if self.is_active:
            pygame.draw.rect(screen, VisualTheme.success_background, pill, border_radius=11)
            pygame.draw.rect(screen, VisualTheme.success_border, pill, width=1, border_radius=11)
            state_text, state_color = "Ativo", VisualTheme.success
        else:
            pygame.draw.rect(screen, VisualTheme.neutral_background, pill, border_radius=11)
            pygame.draw.rect(screen, VisualTheme.neutral_border, pill, width=1, border_radius=11)
            state_text, state_color = "Inativo", VisualTheme.text_muted

        state_surface = get_user_interface_font(11, bold=True).render(
            state_text,
            True,
            state_color,
        )
        screen.blit(state_surface, state_surface.get_rect(center=pill.center))
