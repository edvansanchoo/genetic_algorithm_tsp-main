import random
import unittest

from delivery_simulation.models import DEPOT_ID, DeliveryTask
from delivery_simulation.road_network import build_road_network
from delivery_simulation.vehicle_genetic import initialize_vehicle_genetic, run_vehicle_generation


class VehicleGeneticTests(unittest.TestCase):
    def test_initialize_creates_population_of_permutations(self):
        network = build_road_network(
            {DEPOT_ID: (0.0, 0.0), "A": (3.0, 0.0), "B": (0.0, 4.0)},
            radius=100.0,
        )
        tasks = [DeliveryTask("A", 4), DeliveryTask("B", 4)]
        state = initialize_vehicle_genetic(1, tasks, network, population_size=20, rng=random.Random(0))

        self.assertEqual(len(state.population), 20)
        self.assertEqual(len(state.population[0]), 2)
        self.assertLess(state.best_distance, float("inf"))

    def test_generation_does_not_worsen_best(self):
        network = build_road_network(
            {DEPOT_ID: (0.0, 0.0), "A": (3.0, 0.0), "B": (0.0, 4.0)},
            radius=100.0,
        )
        tasks = [DeliveryTask("A", 4), DeliveryTask("B", 4)]
        state = initialize_vehicle_genetic(1, tasks, network, population_size=30, rng=random.Random(1))
        initial_best = state.best_distance

        for _ in range(5):
            run_vehicle_generation(state, network, mutation_probability=0.2, population_size=30)

        self.assertLessEqual(state.best_distance, initial_best)

    def test_tracks_second_best_distinct_from_best(self):
        network = build_road_network(
            {DEPOT_ID: (0.0, 0.0), "A": (3.0, 0.0), "B": (0.0, 4.0), "C": (4.0, 4.0)},
            radius=100.0,
        )
        tasks = [
            DeliveryTask("A", 2),
            DeliveryTask("B", 2),
            DeliveryTask("C", 2),
        ]
        state = initialize_vehicle_genetic(1, tasks, network, population_size=30, rng=random.Random(7))

        self.assertLess(state.best_distance, float("inf"))
        self.assertLess(state.second_best_distance, float("inf"))
        self.assertGreaterEqual(state.second_best_distance, state.best_distance)
        self.assertNotEqual(state.best_permutation, state.second_best_permutation)
