"""Grafo por raio e pathfinding BFS para a malha de entregas."""

from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

Coordinate = Tuple[float, float]
EdgeKey = Tuple[str, str]


@dataclass
class RoadNetwork:
    nodes: Dict[str, Coordinate]
    edges: List[Tuple[str, str]]
    connection_radius: float


def euclidean(point_a: Coordinate, point_b: Coordinate) -> float:
    return math.hypot(point_a[0] - point_b[0], point_a[1] - point_b[1])


def generate_transit_nodes(
    count: int,
    map_min_x: float,
    map_min_y: float,
    map_max_x: float,
    map_max_y: float,
    existing: Optional[Sequence[Coordinate]] = None,
    min_separation: float = 30.0,
    max_attempts: int = 200,
    rng: Optional[random.Random] = None,
    id_prefix: str = "T",
) -> List[Tuple[str, Coordinate]]:
    """Gera nós com ids T1..Tn (ou prefixo custom) respeitando separação mínima."""
    rng = rng or random.Random()
    placed: List[Coordinate] = list(existing or [])
    result: List[Tuple[str, Coordinate]] = []

    for index in range(1, count + 1):
        chosen: Optional[Coordinate] = None
        for _ in range(max_attempts):
            candidate = (
                rng.uniform(map_min_x, map_max_x),
                rng.uniform(map_min_y, map_max_y),
            )
            if all(euclidean(candidate, other) >= min_separation for other in placed):
                chosen = candidate
                break
        if chosen is None:
            chosen = (
                rng.uniform(map_min_x, map_max_x),
                rng.uniform(map_min_y, map_max_y),
            )
        placed.append(chosen)
        result.append((f"{id_prefix}{index}", chosen))
    return result


def build_radius_graph(nodes: Dict[str, Coordinate], radius: float) -> List[Tuple[str, str]]:
    node_ids = list(nodes.keys())
    edges: List[Tuple[str, str]] = []
    for i, node_a in enumerate(node_ids):
        for node_b in node_ids[i + 1 :]:
            if euclidean(nodes[node_a], nodes[node_b]) <= radius:
                edges.append((node_a, node_b))
    return edges


def build_complete_graph(nodes: Dict[str, Coordinate]) -> List[Tuple[str, str]]:
    node_ids = list(nodes.keys())
    edges: List[Tuple[str, str]] = []
    for index, node_a in enumerate(node_ids):
        for node_b in node_ids[index + 1 :]:
            edges.append((node_a, node_b))
    return edges


def build_complete_network(nodes: Dict[str, Coordinate]) -> RoadNetwork:
    return RoadNetwork(
        nodes=dict(nodes),
        edges=build_complete_graph(nodes),
        connection_radius=0.0,
    )


def build_delivery_hub_network(
    nodes: Dict[str, Coordinate],
    delivery_ids: Sequence[str],
) -> RoadNetwork:
    delivery_set = set(delivery_ids)
    node_ids = list(nodes.keys())
    edges: List[Tuple[str, str]] = []
    for index, node_a in enumerate(node_ids):
        for node_b in node_ids[index + 1 :]:
            if node_a in delivery_set and node_b in delivery_set:
                continue
            edges.append((node_a, node_b))
    return RoadNetwork(
        nodes=dict(nodes),
        edges=edges,
        connection_radius=0.0,
    )


def build_road_network(nodes: Dict[str, Coordinate], radius: float) -> RoadNetwork:
    return RoadNetwork(
        nodes=dict(nodes),
        edges=build_radius_graph(nodes, radius),
        connection_radius=radius,
    )


def _adjacency(network: RoadNetwork) -> Dict[str, List[str]]:
    adjacency: Dict[str, List[str]] = {node_id: [] for node_id in network.nodes}
    for node_a, node_b in network.edges:
        if node_a in adjacency and node_b in adjacency:
            adjacency[node_a].append(node_b)
            adjacency[node_b].append(node_a)
    return adjacency


def path_distance(network: RoadNetwork, path: List[str]) -> float:
    if len(path) < 2:
        return 0.0
    total = 0.0
    for index in range(len(path) - 1):
        total += euclidean(network.nodes[path[index]], network.nodes[path[index + 1]])
    return total


def canonical_edge(node_a: str, node_b: str) -> EdgeKey:
    return (node_a, node_b) if node_a <= node_b else (node_b, node_a)


def edge_cost(
    network: RoadNetwork,
    node_a: str,
    node_b: str,
    used_edges: Set[EdgeKey],
    reuse_penalty: float,
    forbidden_edges: Optional[Set[EdgeKey]] = None,
) -> float:
    forbidden_edges = forbidden_edges or set()
    if canonical_edge(node_a, node_b) in forbidden_edges:
        return float("inf")
    base = euclidean(network.nodes[node_a], network.nodes[node_b])
    if canonical_edge(node_a, node_b) in used_edges:
        return base * reuse_penalty
    return base


def path_weighted_distance(
    network: RoadNetwork,
    path: List[str],
    used_edges: Set[EdgeKey],
    reuse_penalty: float,
) -> float:
    if len(path) < 2:
        return 0.0
    total = 0.0
    for index in range(len(path) - 1):
        total += edge_cost(
            network,
            path[index],
            path[index + 1],
            used_edges,
            reuse_penalty,
        )
    return total


def find_path_weighted(
    network: RoadNetwork,
    origin: str,
    destination: str,
    blocked: Optional[Set[str]] = None,
    used_edges: Optional[Set[EdgeKey]] = None,
    reuse_penalty: float = 1.0,
    forbidden_edges: Optional[Set[EdgeKey]] = None,
    no_through: Optional[Set[str]] = None,
) -> List[str]:
    """Dijkstra; forbidden_edges are impassable; used_edges cost × reuse_penalty."""
    blocked = blocked or set()
    used_edges = used_edges or set()
    forbidden_edges = forbidden_edges or set()
    no_through = no_through or set()
    if origin not in network.nodes or destination not in network.nodes:
        return []
    if origin in blocked or destination in blocked:
        return []
    if origin == destination:
        return [origin]

    adjacency = _adjacency(network)
    dist: Dict[str, float] = {origin: 0.0}
    prev: Dict[str, Optional[str]] = {origin: None}
    heap: List[Tuple[float, str]] = [(0.0, origin)]

    while heap:
        cost, node = heapq.heappop(heap)
        if cost > dist.get(node, float("inf")):
            continue
        if node == destination:
            break
        for neighbor in adjacency.get(node, []):
            if neighbor in blocked:
                continue
            if neighbor in no_through and neighbor != destination:
                continue
            new_cost = cost + edge_cost(
                network,
                node,
                neighbor,
                used_edges,
                reuse_penalty,
                forbidden_edges,
            )
            if new_cost < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_cost
                prev[neighbor] = node
                heapq.heappush(heap, (new_cost, neighbor))

    if destination not in prev:
        return []

    path: List[str] = []
    current: Optional[str] = destination
    while current is not None:
        path.append(current)
        current = prev[current]
    path.reverse()
    return path


def find_path(
    network: RoadNetwork,
    origin: str,
    destination: str,
    blocked: Optional[Set[str]] = None,
    no_through: Optional[Set[str]] = None,
) -> List[str]:
    """BFS; nós em `blocked` não podem ser intermediários nem destino."""
    blocked = blocked or set()
    no_through = no_through or set()
    if origin not in network.nodes or destination not in network.nodes:
        return []
    if origin in blocked or destination in blocked:
        return []
    if origin == destination:
        return [origin]

    adjacency = _adjacency(network)
    queue: List[List[str]] = [[origin]]
    visited = {origin}
    best_path: List[str] = []
    best_length = float("inf")

    while queue:
        path = queue.pop(0)
        current = path[-1]
        for neighbor in adjacency.get(current, []):
            if neighbor in visited:
                continue
            if neighbor in blocked:
                continue
            if neighbor in no_through and neighbor != destination:
                continue
            new_path = path + [neighbor]
            if neighbor == destination:
                length = path_distance(network, new_path)
                if length < best_length:
                    best_length = length
                    best_path = new_path
                continue
            visited.add(neighbor)
            queue.append(new_path)

    return best_path


def is_reachable(
    network: RoadNetwork,
    origin: str,
    destination: str,
    blocked: Optional[Set[str]] = None,
) -> bool:
    return bool(find_path(network, origin, destination, blocked))


def ensure_connectivity(
    network: RoadNetwork,
    root_id: str,
    required_ids: Sequence[str],
    blocked: Optional[Set[str]] = None,
) -> bool:
    return all(is_reachable(network, root_id, node_id, blocked) for node_id in required_ids)


def _add_edge(network: RoadNetwork, node_a: str, node_b: str) -> RoadNetwork:
    edges = list(network.edges)
    pair = (node_a, node_b)
    reverse = (node_b, node_a)
    if pair not in edges and reverse not in edges:
        edges.append(pair)
    return RoadNetwork(
        nodes=dict(network.nodes),
        edges=edges,
        connection_radius=network.connection_radius,
    )


def connect_nearest_neighbor(network: RoadNetwork, node_id: str) -> RoadNetwork:
    if node_id not in network.nodes:
        return network
    origin = network.nodes[node_id]
    nearest_id = None
    nearest_distance = float("inf")
    for other_id, coordinate in network.nodes.items():
        if other_id == node_id:
            continue
        distance = euclidean(origin, coordinate)
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_id = other_id
    if nearest_id is None:
        return network
    return _add_edge(network, node_id, nearest_id)


def build_connected_network(
    nodes: Dict[str, Coordinate],
    radius: float,
    root_id: str,
    required_ids: Sequence[str],
    max_attempts: int = 50,
) -> RoadNetwork:
    network = build_road_network(nodes, radius)
    if ensure_connectivity(network, root_id, required_ids):
        return network

    attempts = max(max_attempts, len(required_ids) * 4)
    for _ in range(attempts):
        for node_id in required_ids:
            if not is_reachable(network, root_id, node_id):
                network = connect_nearest_neighbor(network, node_id)
        if ensure_connectivity(network, root_id, required_ids):
            return network

    for node_id in required_ids:
        if not is_reachable(network, root_id, node_id):
            network = _add_edge(network, root_id, node_id)
    return network
