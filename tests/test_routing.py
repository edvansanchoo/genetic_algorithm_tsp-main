import unittest

from delivery_simulation.models import DeliveryPoint, SimulationConfig
from delivery_simulation.routing import run_greedy_simulation


class GreedyRoutingTests(unittest.TestCase):
    def _make_points(self, spec: dict[str, tuple[tuple[float, float], int]]) -> list[DeliveryPoint]:
        return [
            DeliveryPoint(
                id=point_id,
                coordinate=coordinate,
                total_items=item_count,
                remaining_items=item_count,
            )
            for point_id, (coordinate, item_count) in spec.items()
        ]

    def test_single_vehicle_abc_example_produces_two_trips(self):
        depot = (0.0, 0.0)
        points = self._make_points(
            {
                "A": ((1.0, 0.0), 6),
                "B": ((10.0, 0.0), 8),
                "C": ((2.0, 1.0), 2),
            }
        )
        config = SimulationConfig(vehicle_count=1, delivery_point_count=3, total_items=16)

        result = run_greedy_simulation(config, depot, points)
        vehicle = result.vehicles[0]

        self.assertEqual(len(vehicle.trips), 2)
        delivered_by_point = {point.id: 0 for point in points}
        for trip in vehicle.trips:
            for stop in trip.stops:
                if stop.point_id != "DEPOT":
                    delivered_by_point[stop.point_id] += stop.items_delivered
        self.assertEqual(delivered_by_point, {"A": 6, "B": 8, "C": 2})
        self.assertTrue(all(point.remaining_items == 0 for point in result.delivery_points))
        for trip in vehicle.trips:
            self.assertEqual(trip.stops[0].point_id, "DEPOT")
            self.assertEqual(trip.stops[-1].point_id, "DEPOT")

    def test_partial_delivery_when_point_exceeds_capacity(self):
        depot = (0.0, 0.0)
        points = self._make_points({"A": ((5.0, 0.0), 14)})
        config = SimulationConfig(vehicle_count=1, delivery_point_count=1, total_items=14)

        result = run_greedy_simulation(config, depot, points)
        vehicle = result.vehicles[0]

        self.assertEqual(len(vehicle.trips), 2)
        delivered = [
            (stop.point_id, stop.items_delivered)
            for trip in vehicle.trips
            for stop in trip.stops
            if stop.point_id != "DEPOT"
        ]
        self.assertEqual(delivered, [("A", 10), ("A", 4)])

    def test_all_trips_start_and_end_at_depot(self):
        depot = (0.0, 0.0)
        points = self._make_points({"A": ((3.0, 0.0), 4), "B": ((0.0, 4.0), 4)})
        config = SimulationConfig(vehicle_count=1, delivery_point_count=2, total_items=8)

        result = run_greedy_simulation(config, depot, points)

        for vehicle in result.vehicles:
            for trip in vehicle.trips:
                self.assertEqual(trip.stops[0].point_id, "DEPOT")
                self.assertEqual(trip.stops[-1].point_id, "DEPOT")
                self.assertGreater(trip.distance, 0.0)
