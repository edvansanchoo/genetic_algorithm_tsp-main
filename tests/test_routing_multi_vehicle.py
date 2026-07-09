import unittest

from delivery_simulation.models import DEPOT_ID, DeliveryPoint, SimulationConfig
from delivery_simulation.road_network import build_road_network
from delivery_simulation.routing import run_greedy_simulation


class MultiVehicleRoutingTests(unittest.TestCase):
    def test_two_vehicles_share_pending_deliveries(self):
        depot = (0.0, 0.0)
        points = [
            DeliveryPoint("A", (1.0, 0.0), 4, 4),
            DeliveryPoint("B", (100.0, 0.0), 4, 4),
        ]
        config = SimulationConfig(vehicle_count=2, delivery_point_count=2, total_items=8)
        nodes = {DEPOT_ID: depot, "A": (1.0, 0.0), "B": (100.0, 0.0)}
        network = build_road_network(nodes, 1000.0)

        result = run_greedy_simulation(config, depot, points, network, [])

        self.assertEqual(len(result.vehicles), 2)
        self.assertTrue(all(point.remaining_items == 0 for point in result.delivery_points))
        assigned_union = set(result.vehicles[0].assigned_points + result.vehicles[1].assigned_points)
        self.assertEqual(assigned_union, {"A", "B"})

    def test_never_exceeds_capacity_per_trip(self):
        depot = (0.0, 0.0)
        points = [
            DeliveryPoint("A", (1.0, 0.0), 6, 6),
            DeliveryPoint("B", (2.0, 0.0), 6, 6),
        ]
        config = SimulationConfig(vehicle_count=2, delivery_point_count=2, total_items=12)
        nodes = {DEPOT_ID: depot, "A": (1.0, 0.0), "B": (2.0, 0.0)}
        network = build_road_network(nodes, 1000.0)

        result = run_greedy_simulation(config, depot, points, network, [])

        for vehicle in result.vehicles:
            for trip in vehicle.trips:
                load = 0
                for stop in trip.stops:
                    if stop.point_id != DEPOT_ID:
                        load += stop.items_delivered
                self.assertLessEqual(load, 10)
