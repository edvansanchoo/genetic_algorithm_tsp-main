"""Modelos de árvores e lagos no mapa."""

from dataclasses import dataclass
from typing import Union

import pygame

default_terrain_penalty = 500.0


@dataclass
class TreeObstacle:
    name: str
    center_x: int
    center_y: int
    radius: int
    enabled: bool = False
    penalty: float = default_terrain_penalty
    variant_index: int = 0


@dataclass
class LakeObstacle:
    name: str
    position_x: int
    position_y: int
    width: int
    height: int
    enabled: bool = False
    penalty: float = default_terrain_penalty
    variant_index: int = 0

    @property
    def rectangle(self) -> pygame.Rect:
        return pygame.Rect(self.position_x, self.position_y, self.width, self.height)


Obstacle = Union[TreeObstacle, LakeObstacle]


def terrain_type_label(obstacle: Obstacle) -> str:
    if isinstance(obstacle, TreeObstacle):
        return "Árvore"
    return "Lago"
