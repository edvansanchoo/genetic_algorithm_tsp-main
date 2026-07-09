"""Gera postos de combustível perto da rede existente."""

import math
import random
from typing import Dict, List, Optional

from delivery_simulation.distance import euclidean
from delivery_simulation.fuel.models import (
    FUEL_STATION_ID_PREFIX,
    MAX_STATION_DISTANCE_FROM_NETWORK,
    MIN_STATION_SEPARATION,
    GasStation,
)
from delivery_simulation.models import Coordinate
from delivery_simulation.road_network import build_road_network


def place_gas_stations(
    count: int,
    anchor_nodes: Dict[str, Coordinate],
    map_min_x: float,
    map_min_y: float,
    map_max_x: float,
    map_max_y: float,
    connection_radius: float,
    min_separation: float = MIN_STATION_SEPARATION,
    max_attempts: int = 100,
    rng: Optional[random.Random] = None,
) -> List[GasStation]:
    if count < 1:
        return []

    random_source = rng or random.Random()
    anchors = list(anchor_nodes.items())
    occupied: List[Coordinate] = list(anchor_nodes.values())
    stations: List[GasStation] = []

    for index in range(count):
        station_id = f"{FUEL_STATION_ID_PREFIX}{index + 1}"
        placed = False
        for _ in range(max_attempts):
            _, anchor_coord = random_source.choice(anchors)
            angle = random_source.uniform(0.0, 2.0 * math.pi)
            distance = random_source.uniform(min_separation, MAX_STATION_DISTANCE_FROM_NETWORK)
            candidate = (
                anchor_coord[0] + distance * math.cos(angle),
                anchor_coord[1] + distance * math.sin(angle),
            )
            if not (map_min_x <= candidate[0] <= map_max_x and map_min_y <= candidate[1] <= map_max_y):
                continue
            if any(euclidean(candidate, existing) < min_separation for existing in occupied):
                continue

            trial_nodes = dict(anchor_nodes)
            for existing in stations:
                trial_nodes[existing.id] = existing.coordinate
            trial_nodes[station_id] = candidate
            network = build_road_network(trial_nodes, connection_radius)
            degree = 0
            for node_a, node_b in network.edges:
                if node_a == station_id or node_b == station_id:
                    degree += 1
            if degree == 0:
                continue

            stations.append(GasStation(station_id, candidate))
            occupied.append(candidate)
            placed = True
            break

        if not placed:
            break

    return stations
