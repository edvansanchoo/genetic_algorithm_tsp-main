"""Rede de ruas por raio e pathfinding BFS."""

import random
from collections import deque
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from delivery_simulation.distance import euclidean
from delivery_simulation.models import Coordinate, DEPOT_ID, RoadNetwork, TransitNode


def generate_transit_nodes(
    count: int,
    map_min_x: float,
    map_min_y: float,
    map_max_x: float,
    map_max_y: float,
    min_separation: float = 30.0,
    max_attempts: int = 100,
    rng: Optional[random.Random] = None,
) -> List[TransitNode]:
    if count < 1:
        return []

    random_source = rng or random.Random()
    placed: List[Coordinate] = []
    transit_nodes: List[TransitNode] = []

    for index in range(count):
        node_id = f"T{index + 1}"
        found = False
        for _ in range(max_attempts):
            candidate = (
                random_source.uniform(map_min_x, map_max_x),
                random_source.uniform(map_min_y, map_max_y),
            )
            if all(euclidean(candidate, existing) >= min_separation for existing in placed):
                placed.append(candidate)
                transit_nodes.append(TransitNode(id=node_id, coordinate=candidate))
                found = True
                break
        if not found:
            raise RuntimeError(f"Não foi possível posicionar nó de trânsito {node_id}")

    return transit_nodes


def build_radius_graph(
    nodes: Dict[str, Coordinate],
    radius: float,
) -> List[Tuple[str, str]]:
    node_ids = list(nodes.keys())
    edges: List[Tuple[str, str]] = []
    for index_a, node_a in enumerate(node_ids):
        for node_b in node_ids[index_a + 1:]:
            if euclidean(nodes[node_a], nodes[node_b]) <= radius:
                edges.append((node_a, node_b))
    return edges


def build_road_network(
    nodes: Dict[str, Coordinate],
    radius: float,
) -> RoadNetwork:
    return RoadNetwork(
        nodes=dict(nodes),
        edges=build_radius_graph(nodes, radius),
        connection_radius=radius,
    )


def _build_adjacency(network: RoadNetwork) -> Dict[str, List[str]]:
    adjacency: Dict[str, List[str]] = {node_id: [] for node_id in network.nodes}
    for node_a, node_b in network.edges:
        adjacency[node_a].append(node_b)
        adjacency[node_b].append(node_a)
    for neighbors in adjacency.values():
        neighbors.sort()
    return adjacency


def path_distance(network: RoadNetwork, path: List[str]) -> float:
    if len(path) < 2:
        return 0.0
    total = 0.0
    for index in range(len(path) - 1):
        total += euclidean(network.nodes[path[index]], network.nodes[path[index + 1]])
    return total


def find_path(
    network: RoadNetwork,
    origin: str,
    destination: str,
    blocked: Set[str],
) -> List[str]:
    if origin not in network.nodes or destination not in network.nodes:
        return []

    if origin == destination:
        return [origin]

    adjacency = _build_adjacency(network)
    queue: deque[Tuple[str, List[str]]] = deque([(origin, [origin])])
    visited_paths: Set[str] = {origin}

    best_path: Optional[List[str]] = None
    best_distance = float("inf")

    while queue:
        current_id, path = queue.popleft()
        for neighbor_id in adjacency[current_id]:
            if neighbor_id in path:
                continue
            if neighbor_id in blocked and neighbor_id != destination:
                continue
            if neighbor_id == destination and neighbor_id in blocked and neighbor_id != DEPOT_ID:
                continue

            new_path = path + [neighbor_id]
            if neighbor_id == destination:
                distance = path_distance(network, new_path)
                if distance < best_distance:
                    best_distance = distance
                    best_path = new_path
                continue

            if neighbor_id not in visited_paths:
                visited_paths.add(neighbor_id)
                queue.append((neighbor_id, new_path))

    return best_path or []


def is_reachable(
    network: RoadNetwork,
    origin: str,
    destination: str,
    blocked: FrozenSet[str] = frozenset(),
) -> bool:
    return bool(find_path(network, origin, destination, set(blocked)))


def ensure_connectivity(
    network: RoadNetwork,
    depot_id: str,
    required_ids: List[str],
) -> bool:
    for node_id in required_ids:
        if not is_reachable(network, depot_id, node_id):
            return False
    return True


def connect_nearest_neighbor(network: RoadNetwork, node_id: str) -> RoadNetwork:
    if node_id not in network.nodes:
        return network

    nearest_id = min(
        (other_id for other_id in network.nodes if other_id != node_id),
        key=lambda other_id: euclidean(network.nodes[node_id], network.nodes[other_id]),
    )
    new_edge = (node_id, nearest_id)
    if new_edge in network.edges or (nearest_id, node_id) in network.edges:
        return network

    return RoadNetwork(
        nodes=dict(network.nodes),
        edges=list(network.edges) + [new_edge],
        connection_radius=network.connection_radius,
    )


def _add_edge(network: RoadNetwork, node_a: str, node_b: str) -> RoadNetwork:
    if node_a not in network.nodes or node_b not in network.nodes:
        return network
    new_edge = (node_a, node_b)
    reverse_edge = (node_b, node_a)
    if new_edge in network.edges or reverse_edge in network.edges:
        return network
    return RoadNetwork(
        nodes=dict(network.nodes),
        edges=list(network.edges) + [new_edge],
        connection_radius=network.connection_radius,
    )


def build_connected_network(
    nodes: Dict[str, Coordinate],
    radius: float,
    depot_id: str,
    required_ids: List[str],
    max_attempts: int = 50,
    rng: Optional[random.Random] = None,
) -> Tuple[RoadNetwork, Optional[str]]:
    """Tenta grafo conexo; retorna rede e mensagem de aviso opcional."""
    del rng
    network = build_road_network(nodes, radius)
    if ensure_connectivity(network, depot_id, required_ids):
        return network, None

    warning = "Grafo desconexo: arestas extras adicionadas ao vizinho mais próximo."
    repair_limit = max(max_attempts, len(required_ids) * 4)

    for _ in range(repair_limit):
        if ensure_connectivity(network, depot_id, required_ids):
            return network, warning

        made_progress = False
        for node_id in required_ids:
            if not is_reachable(network, depot_id, node_id):
                network = connect_nearest_neighbor(network, node_id)
                made_progress = True

        if not made_progress:
            break

    for node_id in required_ids:
        if not is_reachable(network, depot_id, node_id):
            network = _add_edge(network, depot_id, node_id)
            warning = "Grafo desconexo: arestas diretas ao depósito adicionadas."

    return network, warning
