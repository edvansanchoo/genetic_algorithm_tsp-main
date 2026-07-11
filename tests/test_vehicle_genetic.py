"""Testes do GA por veículo."""

import unittest

from traveling_salesman_problem.problem.delivery_mesh import delivery_mesh_from_parts
from traveling_salesman_problem.problem.road_network import RoadNetwork
from traveling_salesman_problem.problem.vrp_decoder import DecodedVehiclePlan
from traveling_salesman_problem.problem.vrp_models import (
    DEPOT_ID,
    DeliveryToken,
    Trip,
    TripStop,
)
from traveling_salesman_problem.simulation.vehicle_genetic import (
    initialize_vehicle_genetic,
    plan_has_drawable_trips,
    run_vehicle_generation,
    select_runner_up_plan,
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


    def test_high_mutation_keeps_drawable_best_plan(self):
        state = initialize_vehicle_genetic(
            vehicle_id=0,
            tokens=self.tokens,
            population_size=30,
            depot=self.depot,
            mesh=self.mesh,
            capacity=10,
            priority_weight=0.0,
        )
        self.assertTrue(plan_has_drawable_trips(state.best_plan))
        for _ in range(30):
            state = run_vehicle_generation(
                state,
                depot=self.depot,
                mesh=self.mesh,
                capacity=10,
                priority_weight=0.0,
                mutation_probability=1.0,
            )
        self.assertTrue(plan_has_drawable_trips(state.best_plan))


class RunnerUpSelectionTests(unittest.TestCase):
    def _valid_trip(self, label: str) -> Trip:
        return Trip(
            stops=[
                TripStop(node_id=DEPOT_ID, quantity=0, coordinate=(0.0, 0.0)),
                TripStop(node_id=label, quantity=1, coordinate=(10.0, 0.0)),
                TripStop(node_id=DEPOT_ID, quantity=0, coordinate=(0.0, 0.0)),
            ],
            distance=20.0,
            path_node_ids=[[DEPOT_ID, label, DEPOT_ID]],
        )

    def test_picks_first_valid_alternate(self):
        plan_a = DecodedVehiclePlan(
            trips=[self._valid_trip("A")],
            total_distance=10.0,
            priority_penalty=0.0,
            fitness=10.0,
        )
        plan_b = DecodedVehiclePlan(
            trips=[self._valid_trip("B")],
            total_distance=20.0,
            priority_penalty=0.0,
            fitness=20.0,
        )
        perm_a = [DeliveryToken("A", 1, 5)]
        perm_b = [DeliveryToken("B", 1, 5)]
        evaluated = [(10.0, perm_a, plan_a), (20.0, perm_b, plan_b)]
        runner = select_runner_up_plan(evaluated, perm_a, 10.0)
        self.assertIs(runner, plan_b)

    def test_returns_none_when_only_one_valid(self):
        valid = DecodedVehiclePlan(
            trips=[self._valid_trip("A")],
            total_distance=10.0,
            priority_penalty=0.0,
            fitness=10.0,
        )
        invalid = DecodedVehiclePlan(
            trips=[],
            total_distance=float("inf"),
            priority_penalty=0.0,
            fitness=float("inf"),
        )
        perm_a = [DeliveryToken("A", 1, 5)]
        perm_b = [DeliveryToken("B", 1, 5)]
        evaluated = [(10.0, perm_a, valid), (float("inf"), perm_b, invalid)]
        self.assertIsNone(select_runner_up_plan(evaluated, perm_a, 10.0))


if __name__ == "__main__":
    unittest.main()
