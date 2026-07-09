import unittest

from delivery_simulation.models import DEPOT_ID, DeliveryPoint, SimulationConfig, TransitNode
from delivery_simulation.road_network import build_road_network
from delivery_simulation.routing import run_greedy_simulation


def _full_network(node_coords, radius=1000.0):
    return build_road_network(node_coords, radius)


class RoutingGraphTests(unittest.TestCase):
    def test_movement_expands_transit_stops(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "T1": (5.0, 0.0),
            "A": (10.0, 0.0),
        }
        network = build_road_network(nodes, radius=6.0)
        points = [DeliveryPoint("A", (10.0, 0.0), 4, 4)]
        config = SimulationConfig(1, 1, 4)
        transit = [TransitNode("T1", (5.0, 0.0))]

        result = run_greedy_simulation(config, (0.0, 0.0), points, network, transit)
        stops = result.vehicles[0].trips[0].stops
        stop_ids = [stop.point_id for stop in stops]
        self.assertIn("T1", stop_ids)
        self.assertTrue(any(stop.is_transit for stop in stops))

    def test_trip_has_no_repeated_non_depot_nodes(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "A": (10.0, 0.0),
            "B": (0.0, 10.0),
        }
        network = _full_network(nodes)
        points = [
            DeliveryPoint("A", (10.0, 0.0), 4, 4),
            DeliveryPoint("B", (0.0, 10.0), 4, 4),
        ]
        config = SimulationConfig(1, 2, 8)

        result = run_greedy_simulation(config, (0.0, 0.0), points, network, [])
        for trip in result.vehicles[0].trips:
            non_depot = [s.point_id for s in trip.stops if s.point_id != DEPOT_ID]
            self.assertEqual(len(non_depot), len(set(non_depot)))

    def test_linear_chain_with_transit_completes(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "T1": (10.0, 0.0),
            "T2": (20.0, 0.0),
            "A": (30.0, 0.0),
        }
        network = build_road_network(nodes, radius=11.0)
        points = [DeliveryPoint("A", (30.0, 0.0), 14, 14)]
        config = SimulationConfig(1, 1, 14)
        transit = [
            TransitNode("T1", (10.0, 0.0)),
            TransitNode("T2", (20.0, 0.0)),
        ]

        result = run_greedy_simulation(config, (0.0, 0.0), points, network, transit)
        self.assertEqual(result.delivery_points[0].remaining_items, 0)
        self.assertEqual(len(result.vehicles[0].trips), 2)

    def test_returns_to_depot_when_deliveries_unreachable_this_trip(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "T1": (10.0, 0.0),
            "A": (20.0, 0.0),
            "B": (0.0, 12.0),
        }
        network = build_road_network(nodes, radius=15.0)
        points = [
            DeliveryPoint("A", (20.0, 0.0), 10, 10),
            DeliveryPoint("B", (0.0, 12.0), 6, 6),
        ]
        config = SimulationConfig(1, 2, 16)

        result = run_greedy_simulation(config, (0.0, 0.0), points, network, [TransitNode("T1", (10.0, 0.0))])
        delivered = sum(point.total_items for point in result.delivery_points)
        self.assertEqual(delivered, 16)

    def test_returns_to_depot_through_visited_delivery_node(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "T1": (10.0, 0.0),
            "A": (20.0, 0.0),
            "B": (10.0, 10.0),
        }
        network = build_road_network(nodes, radius=15.0)
        points = [
            DeliveryPoint("A", (20.0, 0.0), 10, 10),
            DeliveryPoint("B", (10.0, 10.0), 6, 6),
        ]
        config = SimulationConfig(1, 2, 16)

        result = run_greedy_simulation(
            config,
            (0.0, 0.0),
            points,
            network,
            [TransitNode("T1", (10.0, 0.0))],
        )
        self.assertEqual(sum(point.total_items for point in result.delivery_points), 16)

    def test_existing_abc_example_still_completes(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "A": (1.0, 0.0),
            "B": (10.0, 0.0),
            "C": (2.0, 1.0),
        }
        network = _full_network(nodes)
        points = [
            DeliveryPoint("A", (1.0, 0.0), 6, 6),
            DeliveryPoint("B", (10.0, 0.0), 8, 8),
            DeliveryPoint("C", (2.0, 1.0), 2, 2),
        ]
        config = SimulationConfig(1, 3, 16)

        result = run_greedy_simulation(config, (0.0, 0.0), points, network, [])
        delivered = {point.id: point.total_items for point in result.delivery_points}
        self.assertEqual(sum(delivered.values()), 16)
