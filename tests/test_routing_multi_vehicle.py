import unittest

from delivery_simulation.models import DeliveryPoint, SimulationConfig
from delivery_simulation.routing import run_greedy_simulation


class MultiVehicleRoutingTests(unittest.TestCase):
    def test_two_vehicles_share_pending_deliveries(self):
        depot = (0.0, 0.0)
        points = [
            DeliveryPoint("A", (1.0, 0.0), 4, 4),
            DeliveryPoint("B", (100.0, 0.0), 4, 4),
        ]
        config = SimulationConfig(vehicle_count=2, delivery_point_count=2, total_items=8)

        result = run_greedy_simulation(config, depot, points)

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

        result = run_greedy_simulation(config, depot, points)

        for vehicle in result.vehicles:
            for trip in vehicle.trips:
                load = 0
                for stop in trip.stops:
                    if stop.point_id != "DEPOT":
                        load += stop.items_delivered
                self.assertLessEqual(load, 10)
