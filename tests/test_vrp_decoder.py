"""Testes do decoder VRP com capacidade e retorno ao depósito."""

import unittest

from traveling_salesman_problem.problem.delivery_mesh import delivery_mesh_from_parts
from traveling_salesman_problem.problem.road_network import RoadNetwork
from traveling_salesman_problem.problem.vrp_decoder import decode_vehicle_permutation
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, DeliveryToken


def _line_mesh():
    """Malha com corredores alternativos para ida/volta e viagens sem reutilização."""
    network = RoadNetwork(
        nodes={
            DEPOT_ID: (0.0, 0.0),
            "A": (10.0, 0.0),
            "B": (20.0, 0.0),
            "N1": (0.0, 15.0),
            "N2": (10.0, 15.0),
            "N3": (20.0, 15.0),
            "S1": (0.0, -15.0),
            "S2": (10.0, -15.0),
            "S3": (20.0, -15.0),
            "W1": (25.0, 10.0),
            "W2": (5.0, 10.0),
            "E1": (25.0, -10.0),
            "E2": (5.0, -10.0),
        },
        edges=[
            (DEPOT_ID, "A"),
            ("A", "B"),
            (DEPOT_ID, "N1"),
            ("N1", "N2"),
            ("N2", "N3"),
            ("N3", "B"),
            ("A", "N2"),
            ("N2", DEPOT_ID),
            (DEPOT_ID, "S1"),
            ("S1", "S2"),
            ("S2", "S3"),
            ("S3", "B"),
            (DEPOT_ID, "E2"),
            ("E2", "S1"),
            ("B", "W1"),
            ("W1", DEPOT_ID),
            ("B", "W2"),
            ("W2", DEPOT_ID),
            ("B", "E1"),
            ("E1", DEPOT_ID),
        ],
        connection_radius=100.0,
    )
    return delivery_mesh_from_parts(
        network,
        delivery_ids=["A", "B"],
        transit_ids=["N1", "N2", "N3", "S1", "S2", "S3", "W1", "W2", "E1", "E2"],
    )


class VrpDecoderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.depot = (0.0, 0.0)
        self.mesh = _line_mesh()
        self.tokens = [
            DeliveryToken("A", 6, priority=5),
            DeliveryToken("B", 8, priority=9),
        ]

    def test_trip_starts_and_ends_at_depot(self):
        plan = decode_vehicle_permutation(
            self.tokens,
            list(self.tokens),
            self.depot,
            self.mesh,
            capacity=20,
        )
        self.assertTrue(plan.trips)
        for trip in plan.trips:
            self.assertEqual(trip.stops[0].node_id, DEPOT_ID)
            self.assertEqual(trip.stops[-1].node_id, DEPOT_ID)

    def test_capacity_forces_second_trip(self):
        plan = decode_vehicle_permutation(
            self.tokens,
            list(self.tokens),
            self.depot,
            self.mesh,
            capacity=10,
        )
        self.assertEqual(len(plan.trips), 2)
        self.assertTrue(plan.total_distance < float("inf"))

    def test_priority_increases_fitness_when_weight_positive(self):
        base = decode_vehicle_permutation(
            self.tokens,
            list(self.tokens),
            self.depot,
            self.mesh,
            capacity=20,
            priority_weight=0.0,
        )
        weighted = decode_vehicle_permutation(
            self.tokens,
            list(self.tokens),
            self.depot,
            self.mesh,
            capacity=20,
            priority_weight=2.0,
        )
        self.assertAlmostEqual(base.fitness, base.total_distance)
        self.assertGreater(weighted.fitness, weighted.total_distance)
        self.assertAlmostEqual(
            weighted.fitness,
            weighted.total_distance + 2.0 * weighted.priority_penalty,
        )

    def test_invalid_permutation_is_infinite(self):
        bad = [DeliveryToken("A", 6, priority=5)]
        plan = decode_vehicle_permutation(
            self.tokens,
            bad,
            self.depot,
            self.mesh,
            capacity=20,
        )
        self.assertEqual(plan.fitness, float("inf"))


if __name__ == "__main__":
    unittest.main()
