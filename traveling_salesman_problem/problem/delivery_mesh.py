"""Malha de entregas + trânsito + bloqueios para distância TSP."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

from traveling_salesman_problem.problem.road_network import (
    Coordinate,
    EdgeKey,
    RoadNetwork,
    build_delivery_hub_network,
    find_path,
    find_path_weighted,
    generate_transit_nodes,
    path_distance,
    path_weighted_distance,
)
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, DeliveryPoint

MapBounds = Tuple[float, float, float, float]


@dataclass
class DeliveryMesh:
    network: RoadNetwork
    delivery_ids: List[str]
    transit_ids: List[str]
    blocked_ids: Set[str] = field(default_factory=set)
    blocked_coordinates: Dict[str, Coordinate] = field(default_factory=dict)
    coordinate_to_id: Dict[Coordinate, str] = field(default_factory=dict)


def _as_float_coordinate(coordinate: Coordinate) -> Coordinate:
    return (float(coordinate[0]), float(coordinate[1]))


def build_delivery_mesh(
    city_coordinates: Sequence[Coordinate],
    map_bounds: MapBounds,
    transit_count: int,
    blocked_count: int,
    rng: Optional[random.Random] = None,
    rng_seed: Optional[int] = None,
    max_rebuild_attempts: int = 40,
) -> DeliveryMesh:
    if blocked_count < 1:
        raise ValueError("blocked_count must be >= 1")
    if not city_coordinates:
        raise ValueError("city_coordinates must not be empty")

    rng = rng or random.Random(rng_seed)
    min_x, min_y, max_x, max_y = map_bounds
    delivery_coords = [_as_float_coordinate(city) for city in city_coordinates]

    for _ in range(max_rebuild_attempts):
        delivery_ids = [f"D{index}" for index in range(len(delivery_coords))]
        nodes: Dict[str, Coordinate] = {
            delivery_ids[index]: delivery_coords[index]
            for index in range(len(delivery_coords))
        }

        extras = generate_transit_nodes(
            transit_count + blocked_count,
            min_x,
            min_y,
            max_x,
            max_y,
            existing=delivery_coords,
            min_separation=28.0,
            rng=rng,
            id_prefix="N",
        )
        transit_nodes = extras[:transit_count]
        blocked_nodes = extras[transit_count:]

        transit_ids: List[str] = []
        for index, (_raw_id, coordinate) in enumerate(transit_nodes, start=1):
            node_id = f"T{index}"
            transit_ids.append(node_id)
            nodes[node_id] = coordinate

        blocked_ids: Set[str] = set()
        blocked_coordinates: Dict[str, Coordinate] = {}
        for index, (_raw_id, coordinate) in enumerate(blocked_nodes, start=1):
            node_id = f"B{index}"
            blocked_ids.add(node_id)
            blocked_coordinates[node_id] = coordinate

        network = build_delivery_hub_network(nodes, delivery_ids)
        mesh = DeliveryMesh(
            network=network,
            delivery_ids=delivery_ids,
            transit_ids=transit_ids,
            blocked_ids=blocked_ids,
            blocked_coordinates=blocked_coordinates,
            coordinate_to_id={
                network.nodes[node_id]: node_id for node_id in delivery_ids
            },
        )
        if deliveries_mutually_reachable(mesh):
            return mesh

    raise RuntimeError("Could not build reachable delivery mesh")


def build_vrp_mesh(
    depot: Coordinate,
    deliveries: Sequence[DeliveryPoint],
    map_bounds: MapBounds,
    transit_count: int,
    blocked_count: int,
    rng: Optional[random.Random] = None,
    rng_seed: Optional[int] = None,
    max_rebuild_attempts: int = 40,
) -> DeliveryMesh:
    """Malha VRP: depósito + entregas (ids dos pontos) + trânsito; bloqueados só no mapa."""
    if blocked_count < 1:
        raise ValueError("blocked_count must be >= 1")
    if not deliveries:
        raise ValueError("deliveries must not be empty")

    rng = rng or random.Random(rng_seed)
    min_x, min_y, max_x, max_y = map_bounds
    depot_coordinate = _as_float_coordinate(depot)
    delivery_coords = [
        _as_float_coordinate(point.coordinate) for point in deliveries
    ]
    existing = [depot_coordinate, *delivery_coords]

    for _ in range(max_rebuild_attempts):
        delivery_ids = [point.id for point in deliveries]
        nodes: Dict[str, Coordinate] = {DEPOT_ID: depot_coordinate}
        for point, coordinate in zip(deliveries, delivery_coords):
            nodes[point.id] = coordinate

        extras = generate_transit_nodes(
            transit_count + blocked_count,
            min_x,
            min_y,
            max_x,
            max_y,
            existing=existing,
            min_separation=28.0,
            rng=rng,
            id_prefix="N",
        )
        transit_nodes = extras[:transit_count]
        blocked_nodes = extras[transit_count:]

        transit_ids: List[str] = []
        for index, (_raw_id, coordinate) in enumerate(transit_nodes, start=1):
            node_id = f"T{index}"
            transit_ids.append(node_id)
            nodes[node_id] = coordinate

        blocked_ids: Set[str] = set()
        blocked_coordinates: Dict[str, Coordinate] = {}
        for index, (_raw_id, coordinate) in enumerate(blocked_nodes, start=1):
            node_id = f"B{index}"
            blocked_ids.add(node_id)
            blocked_coordinates[node_id] = coordinate

        network = build_delivery_hub_network(nodes, delivery_ids)
        mesh = DeliveryMesh(
            network=network,
            delivery_ids=delivery_ids,
            transit_ids=transit_ids,
            blocked_ids=blocked_ids,
            blocked_coordinates=blocked_coordinates,
            coordinate_to_id={
                network.nodes[node_id]: node_id
                for node_id in [DEPOT_ID, *delivery_ids]
            },
        )
        if depot_reaches_all_deliveries(mesh):
            return mesh

    raise RuntimeError("Could not build reachable VRP mesh")


def depot_reaches_all_deliveries(mesh: DeliveryMesh) -> bool:
    if DEPOT_ID not in mesh.network.nodes:
        return False
    for delivery_id in mesh.delivery_ids:
        if not find_path(mesh.network, DEPOT_ID, delivery_id, set(mesh.blocked_ids)):
            return False
    return True


def delivery_mesh_from_parts(
    network: RoadNetwork,
    delivery_ids: List[str],
    transit_ids: List[str],
    blocked_ids: Optional[Set[str]] = None,
    blocked_coordinates: Optional[Dict[str, Coordinate]] = None,
) -> DeliveryMesh:
    """Helper for unit tests with hand-built networks."""
    return DeliveryMesh(
        network=network,
        delivery_ids=list(delivery_ids),
        transit_ids=list(transit_ids),
        blocked_ids=set(blocked_ids or ()),
        blocked_coordinates=dict(blocked_coordinates or {}),
        coordinate_to_id={
            coordinate: node_id for node_id, coordinate in network.nodes.items()
        },
    )


def _id_for_coordinate(mesh: DeliveryMesh, coordinate: Coordinate) -> str:
    key = _as_float_coordinate(coordinate)
    for coord, node_id in mesh.coordinate_to_id.items():
        if abs(coord[0] - key[0]) < 1e-6 and abs(coord[1] - key[1]) < 1e-6:
            return node_id
    raise KeyError(f"Unknown delivery coordinate: {coordinate}")


def _no_through_for_segment(
    mesh: DeliveryMesh,
    origin_id: str,
    destination_id: str,
) -> Optional[Set[str]]:
    if origin_id in mesh.delivery_ids and destination_id in mesh.delivery_ids:
        return {DEPOT_ID}
    return None


def delivery_segment_path(
    mesh: DeliveryMesh,
    origin: Coordinate,
    destination: Coordinate,
    used_edges: Optional[Set[EdgeKey]] = None,
    reuse_penalty: float = 1.0,
    forbidden_edges: Optional[Set[EdgeKey]] = None,
) -> List[str]:
    origin_id = _id_for_coordinate(mesh, origin)
    destination_id = _id_for_coordinate(mesh, destination)
    return find_path_weighted(
        mesh.network,
        origin_id,
        destination_id,
        blocked=set(mesh.blocked_ids),
        used_edges=used_edges,
        reuse_penalty=reuse_penalty,
        forbidden_edges=forbidden_edges,
        no_through=_no_through_for_segment(mesh, origin_id, destination_id),
    )


def delivery_segment_distance(
    mesh: DeliveryMesh,
    origin: Coordinate,
    destination: Coordinate,
    used_edges: Optional[Set[EdgeKey]] = None,
    reuse_penalty: float = 1.0,
    forbidden_edges: Optional[Set[EdgeKey]] = None,
) -> float:
    path = delivery_segment_path(
        mesh,
        origin,
        destination,
        used_edges=used_edges,
        reuse_penalty=reuse_penalty,
        forbidden_edges=forbidden_edges,
    )
    if not path:
        return float("inf")
    return path_weighted_distance(
        mesh.network,
        path,
        used_edges or set(),
        reuse_penalty,
    )


def deliveries_mutually_reachable(mesh: DeliveryMesh) -> bool:
    if not mesh.delivery_ids:
        return True
    start = mesh.delivery_ids[0]
    for other in mesh.delivery_ids[1:]:
        if not find_path(
            mesh.network,
            start,
            other,
            set(mesh.blocked_ids),
            no_through=_no_through_for_segment(mesh, start, other),
        ):
            return False
    return True


def expand_route_polyline(
    mesh: DeliveryMesh,
    route: Sequence[Coordinate],
) -> List[Coordinate]:
    if len(route) < 2:
        return [_as_float_coordinate(coordinate) for coordinate in route]

    points: List[Coordinate] = []
    for index in range(len(route)):
        origin = route[index]
        destination = route[(index + 1) % len(route)]
        path = delivery_segment_path(mesh, origin, destination)
        if not path:
            return []
        path_coords = [mesh.network.nodes[node_id] for node_id in path]
        if points:
            path_coords = path_coords[1:]
        points.extend(path_coords)
    return points
