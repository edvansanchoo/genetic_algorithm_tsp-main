"""Botão de ação com rótulo e subtítulo opcional."""

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.visualization.fonts import get_user_interface_font


def _mouse_over_rectangle(rectangle: pygame.Rect) -> bool:
    return rectangle.collidepoint(pygame.mouse.get_pos())


class ActionButton:
    def __init__(
        self,
        position_x: int,
        position_y: int,
        width: int,
        height: int,
        label: str,
        subtitle: str = "",
    ) -> None:
        self.rectangle = pygame.Rect(position_x, position_y, width, height)
        self.label = label
        self.subtitle = subtitle
        self.was_pressed = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rectangle.collidepoint(event.pos):
                self.was_pressed = True
                return True
        return False

    def draw(self, screen: pygame.Surface) -> None:
        is_hovered = _mouse_over_rectangle(self.rectangle)
        background_color = VisualTheme.accent_hover if is_hovered else VisualTheme.accent
        pygame.draw.rect(screen, background_color, self.rectangle, border_radius=8)
        pygame.draw.rect(
            screen,
            VisualTheme.border_strong,
            self.rectangle,
            width=1,
            border_radius=8,
        )

        if self.subtitle:
            title_surface = get_user_interface_font(13, bold=True).render(
                self.label,
                True,
                VisualTheme.text_inverse,
            )
            subtitle_surface = get_user_interface_font(10).render(
                self.subtitle,
                True,
                (219, 234, 254),
            )
            screen.blit(
                title_surface,
                title_surface.get_rect(center=(self.rectangle.centerx, self.rectangle.centery - 7)),
            )
            screen.blit(
                subtitle_surface,
                subtitle_surface.get_rect(center=(self.rectangle.centerx, self.rectangle.centery + 9)),
            )
        else:
            text_surface = get_user_interface_font(13, bold=True).render(
                self.label,
                True,
                VisualTheme.text_inverse,
            )
            screen.blit(text_surface, text_surface.get_rect(center=self.rectangle.center))
