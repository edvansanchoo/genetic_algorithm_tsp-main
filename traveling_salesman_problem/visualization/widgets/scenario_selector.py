"""Seletor de cenário com botões estilo rádio e scroll interno."""

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.genetic_algorithm.predefined_problems import SCENARIO_PRESETS
from traveling_salesman_problem.visualization.application_layout import draw_card
from traveling_salesman_problem.visualization.fonts import get_user_interface_font


class ScenarioSelector:
    OPTION_HEIGHT = 28
    OPTION_GAP = 4
    SCROLL_STEP = 32
    SCROLLBAR_WIDTH = 4

    def __init__(
        self,
        position_x: int,
        position_y: int,
        width: int,
        viewport_height: int,
        active_scenario_id: str = "random",
    ) -> None:
        self.position_x = position_x
        self.position_y = position_y
        self.width = width
        self.viewport_height = viewport_height
        self.active_scenario_id = active_scenario_id
        self.was_changed = False
        self.scroll_offset = 0.0
        self._scenario_ids = list(SCENARIO_PRESETS.keys())

    @property
    def height(self) -> int:
        return self.viewport_height

    @property
    def content_height(self) -> int:
        count = len(self._scenario_ids)
        return count * self.OPTION_HEIGHT + max(0, count - 1) * self.OPTION_GAP

    @property
    def max_scroll(self) -> float:
        return max(0.0, float(self.content_height - self.viewport_height))

    @property
    def viewport_rectangle(self) -> pygame.Rect:
        return pygame.Rect(self.position_x, self.position_y, self.width, self.viewport_height)

    def set_active(self, scenario_id: str) -> None:
        self.active_scenario_id = scenario_id
        self._ensure_active_option_visible()

    def clamp_scroll(self) -> None:
        self.scroll_offset = max(0.0, min(self.scroll_offset, self.max_scroll))

    def is_mouse_in_viewport(self, content_position: tuple[int, int]) -> bool:
        return self.viewport_rectangle.collidepoint(content_position)

    def handle_wheel(self, wheel_delta: int, content_position: tuple[int, int]) -> bool:
        if not self.is_mouse_in_viewport(content_position) or self.max_scroll <= 0:
            return False
        self.scroll_offset -= wheel_delta * self.SCROLL_STEP
        self.clamp_scroll()
        return True

    def _option_rectangle(self, index: int) -> pygame.Rect:
        return pygame.Rect(
            self.position_x,
            self.position_y + index * (self.OPTION_HEIGHT + self.OPTION_GAP) - int(self.scroll_offset),
            self.width - self.SCROLLBAR_WIDTH - 4,
            self.OPTION_HEIGHT,
        )

    def _ensure_active_option_visible(self) -> None:
        if self.active_scenario_id not in self._scenario_ids:
            return
        active_index = self._scenario_ids.index(self.active_scenario_id)
        option_top = active_index * (self.OPTION_HEIGHT + self.OPTION_GAP)
        option_bottom = option_top + self.OPTION_HEIGHT
        visible_top = int(self.scroll_offset)
        visible_bottom = visible_top + self.viewport_height
        if option_top < visible_top:
            self.scroll_offset = float(option_top)
        elif option_bottom > visible_bottom:
            self.scroll_offset = float(option_bottom - self.viewport_height)
        self.clamp_scroll()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        if not self.is_mouse_in_viewport(event.pos):
            return
        for index, scenario_id in enumerate(self._scenario_ids):
            option_rect = self._option_rectangle(index)
            if option_rect.collidepoint(event.pos):
                if scenario_id != self.active_scenario_id:
                    self.active_scenario_id = scenario_id
                    self.was_changed = True
                return

    def draw(self, screen: pygame.Surface) -> None:
        label_font = get_user_interface_font(12)
        previous_clip = screen.get_clip()
        screen.set_clip(self.viewport_rectangle)
        for index, scenario_id in enumerate(self._scenario_ids):
            option_rect = self._option_rectangle(index)
            if option_rect.bottom < self.position_y or option_rect.top > self.position_y + self.viewport_height:
                continue
            is_active = scenario_id == self.active_scenario_id
            draw_card(screen, option_rect)
            if is_active:
                pygame.draw.rect(
                    screen,
                    VisualTheme.accent,
                    option_rect,
                    width=2,
                    border_radius=8,
                )
            preset = SCENARIO_PRESETS[scenario_id]
            text_color = VisualTheme.text_primary if is_active else VisualTheme.text_muted
            screen.blit(
                label_font.render(preset.label, True, text_color),
                (option_rect.x + 12, option_rect.centery - 7),
            )
        screen.set_clip(previous_clip)
        self._draw_scrollbar(screen)

    def _draw_scrollbar(self, screen: pygame.Surface) -> None:
        if self.content_height <= self.viewport_height:
            return
        track_x = self.position_x + self.width - self.SCROLLBAR_WIDTH
        track = pygame.Rect(track_x, self.position_y, self.SCROLLBAR_WIDTH, self.viewport_height)
        thumb_height = max(20, int(track.height * self.viewport_height / self.content_height))
        scrollable_track = track.height - thumb_height
        scroll_ratio = 0.0 if self.max_scroll == 0 else self.scroll_offset / self.max_scroll
        thumb_y = track.y + int(scrollable_track * scroll_ratio)
        thumb = pygame.Rect(track.x, thumb_y, track.width, thumb_height)
        pygame.draw.rect(screen, VisualTheme.neutral_background, track, border_radius=2)
        pygame.draw.rect(screen, VisualTheme.neutral, thumb, border_radius=2)
