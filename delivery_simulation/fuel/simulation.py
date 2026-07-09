"""Simula consumo de combustível e desvios a postos em um trecho."""

from dataclasses import dataclass, field
from typing import List, Optional, Set

from delivery_simulation.fuel.models import MAX_FUEL, FuelLeg, FuelStopEvent
from delivery_simulation.models import RoadNetwork
from delivery_simulation.road_network import find_path, path_distance


@dataclass
class FuelTravelResult:
    paths: List[List[str]] = field(default_factory=list)
    fuel_after: float = 0.0
    visited_stations: Set[str] = field(default_factory=set)
    legs: List[FuelLeg] = field(default_factory=list)
    stops: List[FuelStopEvent] = field(default_factory=list)
    is_feasible: bool = True
    distance: float = 0.0


def travel_with_fuel(
    network: RoadNetwork,
    origin: str,
    destination: str,
    fuel: float,
    station_ids: Set[str],
    visited_stations: Set[str],
    blocked: Set[str],
    leg_index_start: int = 0,
) -> FuelTravelResult:
    result = FuelTravelResult(fuel_after=fuel, visited_stations=set(visited_stations))
    direct = find_path(network, origin, destination, blocked)
    if not direct:
        result.is_feasible = False
        return result

    direct_distance = path_distance(network, direct)
    if fuel >= direct_distance:
        fuel_after = fuel - direct_distance
        result.paths = [direct]
        result.fuel_after = fuel_after
        result.distance = direct_distance
        result.legs = [
            FuelLeg(
                leg_index_start,
                origin,
                destination,
                direct_distance,
                fuel,
                direct_distance,
                fuel_after,
            )
        ]
        return result

    best: Optional[tuple[float, str, List[str], List[str]]] = None
    for station_id in station_ids:
        if station_id in visited_stations:
            continue
        path_to_station = find_path(network, origin, station_id, blocked)
        if not path_to_station:
            continue
        dist_to_station = path_distance(network, path_to_station)
        if fuel < dist_to_station:
            continue
        blocked_after = set(blocked) | {station_id}
        path_from_station = find_path(network, station_id, destination, blocked_after)
        if not path_from_station:
            continue
        dist_from_station = path_distance(network, path_from_station)
        total = dist_to_station + dist_from_station
        if best is None or total < best[0]:
            best = (total, station_id, path_to_station, path_from_station)

    if best is None:
        result.is_feasible = False
        return result

    _, station_id, path_to_station, path_from_station = best
    dist_to_station = path_distance(network, path_to_station)
    dist_from_station = path_distance(network, path_from_station)
    fuel_on_arrival = fuel - dist_to_station
    fuel_on_departure = MAX_FUEL
    fuel_after = fuel_on_departure - dist_from_station

    result.paths = [path_to_station, path_from_station]
    result.fuel_after = fuel_after
    result.visited_stations.add(station_id)
    result.distance = dist_to_station + dist_from_station
    result.stops = [
        FuelStopEvent(station_id, fuel_on_arrival, fuel_on_departure),
    ]
    result.legs = [
        FuelLeg(
            leg_index_start,
            origin,
            station_id,
            dist_to_station,
            fuel,
            dist_to_station,
            fuel_on_arrival,
        ),
        FuelLeg(
            leg_index_start + 1,
            station_id,
            destination,
            dist_from_station,
            fuel_on_departure,
            dist_from_station,
            fuel_after,
        ),
    ]
    return result
