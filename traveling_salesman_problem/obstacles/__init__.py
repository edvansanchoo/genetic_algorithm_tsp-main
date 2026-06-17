from traveling_salesman_problem.obstacles.collision import (
    point_inside_any_terrain_feature,
    point_inside_terrain_feature,
    segment_intersects_circle,
    segment_intersects_terrain_feature,
    terrain_features_overlap,
)
from traveling_salesman_problem.obstacles.models import (
    LakeObstacle,
    Obstacle,
    TreeObstacle,
    default_terrain_penalty,
)
from traveling_salesman_problem.obstacles.penalty import calculate_segment_terrain_penalty
from traveling_salesman_problem.obstacles.placement import (
    generate_terrain_features_by_type,
    reshuffle_terrain_feature_positions,
    sync_terrain_feature_counts,
)

__all__ = [
    "LakeObstacle",
    "Obstacle",
    "TreeObstacle",
    "calculate_segment_terrain_penalty",
    "default_terrain_penalty",
    "generate_terrain_features_by_type",
    "point_inside_any_terrain_feature",
    "point_inside_terrain_feature",
    "reshuffle_terrain_feature_positions",
    "segment_intersects_circle",
    "segment_intersects_terrain_feature",
    "sync_terrain_feature_counts",
    "terrain_features_overlap",
]
