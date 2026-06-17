"""Geração, sincronização e reposicionamento de árvores e lagos no mapa."""

import random
from typing import List, Tuple

from traveling_salesman_problem.obstacles.collision import terrain_features_overlap
from traveling_salesman_problem.obstacles.models import LakeObstacle, Obstacle, TreeObstacle


def _overlaps_any_existing_feature(
    candidate: Obstacle,
    existing_features: List[Obstacle],
) -> bool:
    return any(
        terrain_features_overlap(candidate, other_feature)
        for other_feature in existing_features
    )


def renumber_terrain_features(terrain_features: List[Obstacle]) -> None:
    tree_counter = 1
    lake_counter = 1

    for feature in terrain_features:
        if isinstance(feature, TreeObstacle):
            feature.name = f"Árvore {tree_counter}"
            tree_counter += 1
        else:
            feature.name = f"Lago {lake_counter}"
            lake_counter += 1


def _split_terrain_by_type(
    terrain_features: List[Obstacle],
) -> Tuple[List[TreeObstacle], List[LakeObstacle]]:
    trees = [feature for feature in terrain_features if isinstance(feature, TreeObstacle)]
    lakes = [feature for feature in terrain_features if isinstance(feature, LakeObstacle)]
    return trees, lakes


def _sort_terrain_by_type(terrain_features: List[Obstacle]) -> None:
    trees, lakes = _split_terrain_by_type(terrain_features)
    terrain_features.clear()
    terrain_features.extend(trees)
    terrain_features.extend(lakes)
    renumber_terrain_features(terrain_features)


def _try_place_tree(
    map_minimum_x: int,
    map_minimum_y: int,
    map_maximum_x: int,
    map_maximum_y: int,
    existing_features: List[Obstacle],
    enabled: bool,
    maximum_attempts: int = 200,
) -> TreeObstacle:
    for _ in range(maximum_attempts):
        radius = random.randint(25, 55)
        center_x = random.randint(map_minimum_x + radius, map_maximum_x - radius)
        center_y = random.randint(map_minimum_y + radius, map_maximum_y - radius)
        candidate = TreeObstacle(
            name="",
            center_x=center_x,
            center_y=center_y,
            radius=radius,
            enabled=enabled,
            variant_index=random.randint(0, 2),
        )
        if not _overlaps_any_existing_feature(candidate, existing_features):
            return candidate

    radius = random.randint(18, 30)
    center_x = random.randint(map_minimum_x + radius, map_maximum_x - radius)
    center_y = random.randint(map_minimum_y + radius, map_maximum_y - radius)
    return TreeObstacle(
        name="",
        center_x=center_x,
        center_y=center_y,
        radius=radius,
        enabled=enabled,
        variant_index=random.randint(0, 2),
    )


def _try_place_lake(
    map_minimum_x: int,
    map_minimum_y: int,
    map_maximum_x: int,
    map_maximum_y: int,
    existing_features: List[Obstacle],
    enabled: bool,
    maximum_attempts: int = 200,
) -> LakeObstacle:
    for _ in range(maximum_attempts):
        width = random.randint(70, 140)
        height = random.randint(50, 90)
        position_x = random.randint(map_minimum_x, map_maximum_x - width)
        position_y = random.randint(map_minimum_y, map_maximum_y - height)
        candidate = LakeObstacle(
            name="",
            position_x=position_x,
            position_y=position_y,
            width=width,
            height=height,
            enabled=enabled,
            variant_index=random.randint(0, 2),
        )
        if not _overlaps_any_existing_feature(candidate, existing_features):
            return candidate

    width = random.randint(55, 85)
    height = random.randint(40, 65)
    position_x = random.randint(map_minimum_x, map_maximum_x - width)
    position_y = random.randint(map_minimum_y, map_maximum_y - height)
    return LakeObstacle(
        name="",
        position_x=position_x,
        position_y=position_y,
        width=width,
        height=height,
        enabled=enabled,
        variant_index=random.randint(0, 2),
    )


def generate_terrain_features_by_type(
    tree_count: int,
    lake_count: int,
    map_minimum_x: int,
    map_minimum_y: int,
    map_maximum_x: int,
    map_maximum_y: int,
    enabled: bool = False,
) -> List[Obstacle]:
    """Cria uma lista nova com a quantidade solicitada de árvores e lagos."""
    terrain_features: List[Obstacle] = []

    for _ in range(tree_count):
        tree = _try_place_tree(
            map_minimum_x,
            map_minimum_y,
            map_maximum_x,
            map_maximum_y,
            terrain_features,
            enabled,
        )
        terrain_features.append(tree)

    for _ in range(lake_count):
        lake = _try_place_lake(
            map_minimum_x,
            map_minimum_y,
            map_maximum_x,
            map_maximum_y,
            terrain_features,
            enabled,
        )
        terrain_features.append(lake)

    renumber_terrain_features(terrain_features)
    _sort_terrain_by_type(terrain_features)
    return terrain_features


def sync_terrain_feature_counts(
    terrain_features: List[Obstacle],
    tree_count: int,
    lake_count: int,
    map_minimum_x: int,
    map_minimum_y: int,
    map_maximum_x: int,
    map_maximum_y: int,
) -> None:
    """Ajusta a quantidade de cada tipo preservando os que permanecem."""
    trees, lakes = _split_terrain_by_type(terrain_features)

    while len(trees) > tree_count:
        removed = trees.pop()
        terrain_features.remove(removed)

    while len(trees) < tree_count:
        tree = _try_place_tree(
            map_minimum_x,
            map_minimum_y,
            map_maximum_x,
            map_maximum_y,
            terrain_features,
            enabled=False,
        )
        terrain_features.append(tree)
        trees.append(tree)

    while len(lakes) > lake_count:
        removed = lakes.pop()
        terrain_features.remove(removed)

    while len(lakes) < lake_count:
        lake = _try_place_lake(
            map_minimum_x,
            map_minimum_y,
            map_maximum_x,
            map_maximum_y,
            terrain_features,
            enabled=False,
        )
        terrain_features.append(lake)
        lakes.append(lake)

    renumber_terrain_features(terrain_features)
    _sort_terrain_by_type(terrain_features)


def reshuffle_terrain_feature_positions(
    terrain_features: List[Obstacle],
    map_minimum_x: int,
    map_minimum_y: int,
    map_maximum_x: int,
    map_maximum_y: int,
) -> None:
    """Sorteia novas posições mantendo tipo, quantidade e estado habilitado."""
    shuffled = list(terrain_features)
    random.shuffle(shuffled)
    placed: List[Obstacle] = []

    for feature in shuffled:
        enabled = feature.enabled
        variant_index = feature.variant_index
        if isinstance(feature, TreeObstacle):
            new_feature = _try_place_tree(
                map_minimum_x,
                map_minimum_y,
                map_maximum_x,
                map_maximum_y,
                placed,
                enabled,
            )
            new_feature.variant_index = variant_index
        else:
            new_feature = _try_place_lake(
                map_minimum_x,
                map_minimum_y,
                map_maximum_x,
                map_maximum_y,
                placed,
                enabled,
            )
            new_feature.variant_index = variant_index
        placed.append(new_feature)

    terrain_features.clear()
    terrain_features.extend(placed)
    _sort_terrain_by_type(terrain_features)


generate_obstacles_by_type = generate_terrain_features_by_type
sync_obstacle_counts = sync_terrain_feature_counts
reshuffle_obstacle_positions = reshuffle_terrain_feature_positions
