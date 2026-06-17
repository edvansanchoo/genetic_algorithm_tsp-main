"""Painel de controle de árvores, lagos e penalidades de terreno."""

from typing import List

import pygame

from traveling_salesman_problem.obstacles.models import (
    LakeObstacle,
    Obstacle,
    TreeObstacle,
    default_terrain_penalty,
)
from traveling_salesman_problem.visualization.widgets.mutation_slider import MutationSlider
from traveling_salesman_problem.visualization.widgets.toggle_button import ToggleButton


class TerrainTypePenaltySlider(MutationSlider):
    SLIDER_HEIGHT = 52

    def __init__(
        self,
        control_panel: "TerrainControlPanel",
        terrain_type: type,
        position_x: int,
        position_y: int,
        width: int,
        label: str,
    ) -> None:
        self.control_panel = control_panel
        self.terrain_type = terrain_type
        initial_penalty = self._read_penalty_from_terrain()
        super().__init__(
            position_x,
            position_y,
            width,
            self.SLIDER_HEIGHT,
            initial_penalty,
            0,
            2000,
            label,
            " pixels",
        )

    def _features_of_type(self) -> List[Obstacle]:
        return [
            feature
            for feature in self.control_panel.terrain_features
            if isinstance(feature, self.terrain_type)
        ]

    def _read_penalty_from_terrain(self) -> float:
        matching_features = self._features_of_type()
        return matching_features[0].penalty if matching_features else default_terrain_penalty

    def synchronize_from_terrain(self) -> None:
        self.value = self._read_penalty_from_terrain()

    def apply_penalty_to_terrain(self) -> None:
        penalty_value = float(self.integer_value)
        for feature in self._features_of_type():
            feature.penalty = penalty_value

    @property
    def integer_value(self) -> int:
        return int(round(self.value))

    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)
        self.apply_penalty_to_terrain()


class TerrainControlPanel:
    ROW_HEIGHT = 32
    ROW_GAP = 6
    PENALTY_GAP = 8
    SECTION_INNER_GAP = 6

    def __init__(
        self,
        position_x: int,
        position_y: int,
        width: int,
        terrain_features: List[Obstacle],
    ) -> None:
        self.position_x = position_x
        self.position_y = position_y
        self.width = width
        self.terrain_features = terrain_features
        self._create_widgets()

    def _create_widgets(self) -> None:
        current_y = self.position_y

        self.global_penalty_toggle = ToggleButton(
            self.position_x,
            current_y,
            self.width,
            self.ROW_HEIGHT,
            "Evitar árvores e lagos no algoritmo",
            is_active=False,
        )
        current_y += self.ROW_HEIGHT + self.SECTION_INNER_GAP + 4

        self.tree_visibility_toggle = ToggleButton(
            self.position_x,
            current_y,
            self.width,
            self.ROW_HEIGHT,
            "Árvores no mapa",
            is_active=False,
        )
        current_y += self.ROW_HEIGHT + self.ROW_GAP

        self.tree_penalty_slider = TerrainTypePenaltySlider(
            self,
            TreeObstacle,
            self.position_x,
            current_y,
            self.width,
            "Penalidade das árvores",
        )
        current_y += TerrainTypePenaltySlider.SLIDER_HEIGHT + self.PENALTY_GAP

        self.lake_visibility_toggle = ToggleButton(
            self.position_x,
            current_y,
            self.width,
            self.ROW_HEIGHT,
            "Lagos no mapa",
            is_active=False,
        )
        current_y += self.ROW_HEIGHT + self.ROW_GAP

        self.lake_penalty_slider = TerrainTypePenaltySlider(
            self,
            LakeObstacle,
            self.position_x,
            current_y,
            self.width,
            "Penalidade dos lagos",
        )
        self._bottom_y = current_y + TerrainTypePenaltySlider.SLIDER_HEIGHT

    @property
    def height(self) -> int:
        return self._bottom_y - self.position_y + 8

    @property
    def use_terrain_penalties(self) -> bool:
        return self.global_penalty_toggle.is_active

    use_obstacle_penalties = use_terrain_penalties

    def _tree_features(self) -> List[TreeObstacle]:
        return [feature for feature in self.terrain_features if isinstance(feature, TreeObstacle)]

    def _lake_features(self) -> List[LakeObstacle]:
        return [feature for feature in self.terrain_features if isinstance(feature, LakeObstacle)]

    def _synchronize_type_toggles(self) -> None:
        trees = self._tree_features()
        lakes = self._lake_features()
        self.tree_visibility_toggle.is_active = bool(trees) and all(
            feature.enabled for feature in trees
        )
        self.lake_visibility_toggle.is_active = bool(lakes) and all(
            feature.enabled for feature in lakes
        )

    def _set_terrain_type_enabled(self, terrain_type: type, enabled: bool) -> None:
        for feature in self.terrain_features:
            if isinstance(feature, terrain_type):
                feature.enabled = enabled
        self._synchronize_type_toggles()

    def rebuild(self, terrain_features: List[Obstacle]) -> None:
        self.terrain_features = terrain_features
        self._synchronize_type_toggles()
        self.tree_penalty_slider.synchronize_from_terrain()
        self.lake_penalty_slider.synchronize_from_terrain()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.global_penalty_toggle.handle_event(event):
            return
        if self.tree_visibility_toggle.handle_event(event):
            self._set_terrain_type_enabled(
                TreeObstacle,
                self.tree_visibility_toggle.is_active,
            )
            return
        if self.lake_visibility_toggle.handle_event(event):
            self._set_terrain_type_enabled(
                LakeObstacle,
                self.lake_visibility_toggle.is_active,
            )
            return
        self.tree_penalty_slider.handle_event(event)
        self.lake_penalty_slider.handle_event(event)

    def draw(self, screen: pygame.Surface) -> None:
        self.global_penalty_toggle.draw(screen)
        self.tree_visibility_toggle.draw(screen)
        self.tree_penalty_slider.draw(screen)
        self.lake_visibility_toggle.draw(screen)
        self.lake_penalty_slider.draw(screen)


ObstacleControlPanel = TerrainControlPanel
