"""Viewport scrollável para a sidebar abaixo do gráfico de convergência."""

from __future__ import annotations

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme


class SidebarScrollView:
    SCROLL_STEP = 40
    MIN_THUMB_HEIGHT = 24

    def __init__(
        self,
        viewport_top: int,
        viewport_height: int,
        content_width: int,
    ) -> None:
        self.viewport_top = viewport_top
        self.viewport_height = viewport_height
        self.content_width = content_width
        self.scroll_offset = 0.0
        self.content_height = 0
        self._content_surface: pygame.Surface | None = None
        self._is_dragging_thumb = False
        self._drag_anchor_offset = 0.0

    @property
    def max_scroll(self) -> float:
        return max(0.0, float(self.content_height - self.viewport_height))

    @property
    def content_surface(self) -> pygame.Surface:
        if self._content_surface is None:
            raise RuntimeError("SidebarScrollView content surface not initialized")
        return self._content_surface

    def set_content_height(self, height: int) -> None:
        self.content_height = max(height, self.viewport_height)
        self._content_surface = pygame.Surface((self.content_width, self.content_height))
        self._content_surface.fill(VisualTheme.background_sidebar)
        self.clamp_scroll()

    def clamp_scroll(self) -> None:
        self.scroll_offset = max(0.0, min(self.scroll_offset, self.max_scroll))

    def is_mouse_in_viewport(self, position: tuple[int, int]) -> bool:
        mouse_x, mouse_y = position
        if mouse_x >= VisualTheme.sidebar_width - VisualTheme.scrollbar_width:
            return False
        return self.viewport_top <= mouse_y < self.viewport_top + self.viewport_height

    def translate_position(self, position: tuple[int, int]) -> tuple[int, int]:
        mouse_x, mouse_y = position
        content_y = int(mouse_y - self.viewport_top + self.scroll_offset)
        return mouse_x, content_y

    def translate_event(self, event: pygame.event.Event) -> pygame.event.Event:
        if not hasattr(event, "pos"):
            return event
        translated_position = self.translate_position(event.pos)
        event_dict = event.dict.copy()
        event_dict["pos"] = translated_position
        return pygame.event.Event(event.type, event_dict)

    def _track_rectangle(self) -> pygame.Rect:
        track_x = VisualTheme.sidebar_width - VisualTheme.scrollbar_width - 4
        return pygame.Rect(track_x, self.viewport_top + 4, VisualTheme.scrollbar_width, self.viewport_height - 8)

    def _thumb_rectangle(self) -> pygame.Rect:
        track = self._track_rectangle()
        if self.content_height <= self.viewport_height:
            return pygame.Rect(track.x, track.y, track.width, track.height)

        thumb_height = max(
            self.MIN_THUMB_HEIGHT,
            int(track.height * self.viewport_height / self.content_height),
        )
        scrollable_track = track.height - thumb_height
        thumb_ratio = 0.0 if self.max_scroll == 0 else self.scroll_offset / self.max_scroll
        thumb_y = track.y + int(scrollable_track * thumb_ratio)
        return pygame.Rect(track.x, thumb_y, track.width, thumb_height)

    def _scroll_from_thumb_position(self, thumb_y: int) -> None:
        track = self._track_rectangle()
        thumb = self._thumb_rectangle()
        scrollable_track = track.height - thumb.height
        if scrollable_track <= 0:
            self.scroll_offset = 0.0
            return
        relative_y = max(0, min(thumb_y - track.y, scrollable_track))
        self.scroll_offset = (relative_y / scrollable_track) * self.max_scroll
        self.clamp_scroll()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEWHEEL:
            if self.is_mouse_in_viewport(pygame.mouse.get_pos()):
                self.scroll_offset -= event.y * self.SCROLL_STEP
                self.clamp_scroll()
                return True
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            thumb_rectangle = self._thumb_rectangle()
            if thumb_rectangle.collidepoint(event.pos):
                self._is_dragging_thumb = True
                self._drag_anchor_offset = event.pos[1] - thumb_rectangle.y
                return True
            track_rectangle = self._track_rectangle()
            if track_rectangle.collidepoint(event.pos) and self.max_scroll > 0:
                new_thumb_y = event.pos[1] - self._thumb_rectangle().height // 2
                self._scroll_from_thumb_position(new_thumb_y)
                return True
            return False

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._is_dragging_thumb:
                self._is_dragging_thumb = False
                return True
            return False

        if event.type == pygame.MOUSEMOTION and self._is_dragging_thumb:
            new_thumb_y = event.pos[1] - self._drag_anchor_offset
            self._scroll_from_thumb_position(new_thumb_y)
            return True

        return False

    def blit_to_screen(self, screen: pygame.Surface) -> None:
        if self._content_surface is None:
            return

        source_y = int(self.scroll_offset)
        visible_height = min(self.viewport_height, self.content_height - source_y)
        if visible_height <= 0:
            return

        source_rectangle = pygame.Rect(0, source_y, self.content_width, visible_height)
        destination_rectangle = pygame.Rect(0, self.viewport_top, self.content_width, visible_height)
        screen.blit(self._content_surface, destination_rectangle, source_rectangle)

        pygame.draw.line(
            screen,
            VisualTheme.divider,
            (0, self.viewport_top - 1),
            (VisualTheme.sidebar_width, self.viewport_top - 1),
            1,
        )
        pygame.draw.line(
            screen,
            VisualTheme.divider,
            (0, self.viewport_top + self.viewport_height),
            (VisualTheme.sidebar_width, self.viewport_top + self.viewport_height),
            1,
        )

        self._draw_scrollbar(screen)

    def _draw_scrollbar(self, screen: pygame.Surface) -> None:
        if self.content_height <= self.viewport_height:
            return

        track = self._track_rectangle()
        thumb = self._thumb_rectangle()
        pygame.draw.rect(screen, VisualTheme.neutral_background, track, border_radius=3)
        pygame.draw.rect(screen, VisualTheme.neutral, thumb, border_radius=3)
