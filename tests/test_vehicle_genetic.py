"""Testes do GA por veículo."""

import unittest

from traveling_salesman_problem.problem.delivery_mesh import delivery_mesh_from_parts
from traveling_salesman_problem.problem.road_network import RoadNetwork
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, DeliveryToken
from traveling_salesman_problem.simulation.vehicle_genetic import (
    initialize_vehicle_genetic,
    run_vehicle_generation,
)


class VehicleGeneticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.depot = (0.0, 0.0)
        network = RoadNetwork(
            nodes={
                DEPOT_ID: (0.0, 0.0),
                "A": (10.0, 0.0),
                "B": (20.0, 0.0),
                "C": (10.0, 10.0),
            },
            edges=[
                (DEPOT_ID, "A"),
                (DEPOT_ID, "C"),
                ("A", "B"),
                ("A", "C"),
                ("B", "C"),
            ],
            connection_radius=20.0,
        )
        self.mesh = delivery_mesh_from_parts(
            network,
            delivery_ids=["A", "B", "C"],
            transit_ids=[],
        )
        self.tokens = [
            DeliveryToken("A", 3, 5),
            DeliveryToken("B", 3, 5),
            DeliveryToken("C", 3, 8),
        ]

    def test_initialize_has_finite_best(self):
        state = initialize_vehicle_genetic(
            vehicle_id=0,
            tokens=self.tokens,
            population_size=20,
            depot=self.depot,
            mesh=self.mesh,
            capacity=10,
            priority_weight=0.0,
        )
        self.assertTrue(state.best_fitness < float("inf"))
        self.assertEqual(len(state.population), 20)

    def test_generations_do_not_worsen_recorded_best(self):
        state = initialize_vehicle_genetic(
            vehicle_id=0,
            tokens=self.tokens,
            population_size=30,
            depot=self.depot,
            mesh=self.mesh,
            capacity=10,
            priority_weight=1.0,
        )
        initial_best = state.best_fitness
        for _ in range(15):
            state = run_vehicle_generation(
                state,
                depot=self.depot,
                mesh=self.mesh,
                capacity=10,
                priority_weight=1.0,
                mutation_probability=0.2,
            )
        self.assertLessEqual(state.best_fitness, initial_best)
        self.assertTrue(state.best_plan is not None)
        self.assertTrue(state.best_plan.trips)


if __name__ == "__main__":
    unittest.main()
