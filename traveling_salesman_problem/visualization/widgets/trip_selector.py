"""Seletor interativo de veículo e viagem."""

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.visualization.fonts import get_user_interface_font


class TripSelector:
    BUTTON_WIDTH = 36
    BUTTON_HEIGHT = 28
    BUTTON_GAP = 4

    def __init__(
        self,
        position_x: int,
        position_y: int,
        width: int,
    ) -> None:
        self.position_x = position_x
        self.position_y = position_y
        self.width = width
        self.enabled = False
        self.vehicle_count = 1
        self.trip_counts: dict[int, int] = {1: 0}
        self.active_vehicle_id = 1
        self.active_trip_index = 0
        self.view_mode = "single"
        self.was_changed = False
        self._buttons: list[tuple[pygame.Rect, str, str]] = []

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def set_vehicle_trip_counts(self, vehicle_count: int, trip_counts: dict[int, int]) -> None:
        self.vehicle_count = vehicle_count
        self.trip_counts = trip_counts
        if self.active_vehicle_id > vehicle_count:
            self.active_vehicle_id = 1
        max_trips = trip_counts.get(self.active_vehicle_id, 0)
        if self.active_trip_index >= max_trips and self.view_mode == "single":
            self.active_trip_index = 0

    def _rebuild_buttons(self) -> None:
        self._buttons = []
        y = self.position_y
        x = self.position_x

        for vehicle_id in range(1, self.vehicle_count + 1):
            rect = pygame.Rect(x, y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
            self._buttons.append((rect, "vehicle", str(vehicle_id)))
            x += self.BUTTON_WIDTH + self.BUTTON_GAP
        y += self.BUTTON_HEIGHT + 8
        x = self.position_x

        trip_count = self.trip_counts.get(self.active_vehicle_id, 0)
        for trip_index in range(trip_count):
            rect = pygame.Rect(x, y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
            self._buttons.append((rect, "trip", str(trip_index)))
            x += self.BUTTON_WIDTH + self.BUTTON_GAP

        all_rect = pygame.Rect(x, y, self.BUTTON_WIDTH + 12, self.BUTTON_HEIGHT)
        self._buttons.append((all_rect, "trip_all", "Todos"))

        y += self.BUTTON_HEIGHT + 8
        single_rect = pygame.Rect(self.position_x, y, 120, self.BUTTON_HEIGHT)
        all_mode_rect = pygame.Rect(self.position_x + 128, y, 140, self.BUTTON_HEIGHT)
        self._buttons.append((single_rect, "mode_single", "Uma viagem"))
        self._buttons.append((all_mode_rect, "mode_all", "Todas"))

    @property
    def height(self) -> int:
        return self.BUTTON_HEIGHT * 3 + 16

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        self._rebuild_buttons()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, kind, value in self._buttons:
                if rect.collidepoint(event.pos):
                    if kind == "vehicle":
                        self.active_vehicle_id = int(value)
                        self.active_trip_index = 0
                        self.was_changed = True
                    elif kind == "trip":
                        self.active_trip_index = int(value)
                        self.view_mode = "single"
                        self.was_changed = True
                    elif kind == "trip_all":
                        self.view_mode = "all"
                        self.was_changed = True
                    elif kind == "mode_single":
                        self.view_mode = "single"
                        self.was_changed = True
                    elif kind == "mode_all":
                        self.view_mode = "all"
                        self.was_changed = True
                    return True
        return False

    def draw(self, screen: pygame.Surface) -> None:
        self._rebuild_buttons()
        label_font = get_user_interface_font(11)
        button_font = get_user_interface_font(11, bold=True)

        screen.blit(
            label_font.render("Veículo:", True, VisualTheme.text_muted),
            (self.position_x, self.position_y - 16),
        )

        for rect, kind, value in self._buttons:
            is_active = False
            if kind == "vehicle":
                is_active = int(value) == self.active_vehicle_id
            elif kind == "trip":
                is_active = self.view_mode == "single" and int(value) == self.active_trip_index
            elif kind == "trip_all":
                is_active = self.view_mode == "all"
            elif kind == "mode_single":
                is_active = self.view_mode == "single"
            elif kind == "mode_all":
                is_active = self.view_mode == "all"

            if not self.enabled:
                color = VisualTheme.neutral_background
                text_color = VisualTheme.text_muted
            elif is_active:
                color = VisualTheme.accent
                text_color = VisualTheme.text_inverse
            else:
                color = VisualTheme.background_card
                text_color = VisualTheme.text_primary

            pygame.draw.rect(screen, color, rect, border_radius=6)
            pygame.draw.rect(screen, VisualTheme.border, rect, width=1, border_radius=6)
            label = "Todas" if value == "Todos" else value
            if kind.startswith("mode"):
                label = value
            text = button_font.render(label, True, text_color)
            screen.blit(text, text.get_rect(center=rect.center))
