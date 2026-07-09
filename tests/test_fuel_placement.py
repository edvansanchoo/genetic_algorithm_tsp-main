import math
import random
import unittest

from delivery_simulation.distance import euclidean
from delivery_simulation.fuel.models import MAX_STATION_DISTANCE_FROM_NETWORK, MIN_STATION_SEPARATION
from delivery_simulation.fuel.placement import place_gas_stations
from delivery_simulation.models import DEPOT_ID
from delivery_simulation.road_network import build_road_network


class FuelPlacementTests(unittest.TestCase):
    def test_stations_within_100px_of_an_anchor(self):
        anchors = {DEPOT_ID: (100.0, 100.0), "A": (200.0, 100.0), "T1": (150.0, 150.0)}
        stations = place_gas_stations(
            3, anchors, 0, 0, 400, 400, connection_radius=120.0, rng=random.Random(1)
        )
        self.assertEqual(len(stations), 3)
        for station in stations:
            nearest = min(euclidean(station.coordinate, coord) for coord in anchors.values())
            self.assertLessEqual(nearest, MAX_STATION_DISTANCE_FROM_NETWORK + 1e-6)

    def test_stations_do_not_overlap_anchors(self):
        anchors = {DEPOT_ID: (100.0, 100.0), "A": (250.0, 100.0)}
        stations = place_gas_stations(
            2, anchors, 0, 0, 400, 400, connection_radius=150.0, rng=random.Random(2)
        )
        for station in stations:
            for coord in anchors.values():
                self.assertGreaterEqual(
                    euclidean(station.coordinate, coord), MIN_STATION_SEPARATION - 1e-6
                )

    def test_stations_connect_in_radius_graph(self):
        anchors = {DEPOT_ID: (0.0, 0.0), "A": (80.0, 0.0), "T1": (40.0, 40.0)}
        radius = 100.0
        stations = place_gas_stations(
            2, anchors, -50, -50, 200, 200, connection_radius=radius, rng=random.Random(3)
        )
        nodes = dict(anchors)
        for station in stations:
            nodes[station.id] = station.coordinate
        network = build_road_network(nodes, radius)
        degree = {node_id: 0 for node_id in network.nodes}
        for a, b in network.edges:
            degree[a] += 1
            degree[b] += 1
        for station in stations:
            self.assertGreater(degree[station.id], 0)

    def test_zero_count_returns_empty(self):
        anchors = {DEPOT_ID: (0.0, 0.0)}
        self.assertEqual(
            place_gas_stations(0, anchors, 0, 0, 100, 100, connection_radius=50.0),
            [],
        )
