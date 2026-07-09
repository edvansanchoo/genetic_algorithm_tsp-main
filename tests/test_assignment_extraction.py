import unittest

from delivery_simulation.assignment import extract_vehicle_assignments
from delivery_simulation.models import (
    DEPOT_ID,
    DeliveryPoint,
    DeliveryTask,
    RoadNetwork,
    SimulationConfig,
    SimulationResult,
    Stop,
    Trip,
    Vehicle,
)


class DeliveryTaskTests(unittest.TestCase):
    def test_task_is_hashable_and_equal(self):
        first = DeliveryTask("A", 10)
        second = DeliveryTask("A", 10)
        self.assertEqual(first, second)
        self.assertEqual(len({first, second}), 1)


class ExtractVehicleAssignmentsTests(unittest.TestCase):
    def test_extracts_delivery_stops_per_vehicle(self):
        network = RoadNetwork(
            nodes={DEPOT_ID: (0.0, 0.0), "A": (1.0, 0.0)},
            edges=[],
            connection_radius=100.0,
        )
        result = SimulationResult(
            config=SimulationConfig(2, 1, 14),
            depot=(0.0, 0.0),
            delivery_points=[DeliveryPoint("A", (1.0, 0.0), 14, 0)],
            vehicles=[
                Vehicle(
                    id=1,
                    current_node_id=DEPOT_ID,
                    current_position=(0.0, 0.0),
                    current_load=0,
                    trips=[
                        Trip(
                            stops=[
                                Stop(DEPOT_ID, 0),
                                Stop("A", 10),
                                Stop(DEPOT_ID, 0),
                            ],
                            distance=20.0,
                        )
                    ],
                ),
                Vehicle(
                    id=2,
                    current_node_id=DEPOT_ID,
                    current_position=(0.0, 0.0),
                    current_load=0,
                    trips=[
                        Trip(
                            stops=[
                                Stop(DEPOT_ID, 0),
                                Stop("A", 4),
                                Stop(DEPOT_ID, 0),
                            ],
                            distance=10.0,
                        )
                    ],
                ),
            ],
            total_system_distance=30.0,
            road_network=network,
            transit_nodes=[],
        )

        assignments = extract_vehicle_assignments(result)

        self.assertEqual(assignments[1], [DeliveryTask("A", 10)])
        self.assertEqual(assignments[2], [DeliveryTask("A", 4)])

    def test_ignores_transit_and_empty_stops(self):
        network = RoadNetwork(
            nodes={DEPOT_ID: (0.0, 0.0), "A": (1.0, 0.0), "T1": (0.5, 0.0)},
            edges=[],
            connection_radius=100.0,
        )
        result = SimulationResult(
            config=SimulationConfig(1, 1, 4),
            depot=(0.0, 0.0),
            delivery_points=[DeliveryPoint("A", (1.0, 0.0), 4, 0)],
            vehicles=[
                Vehicle(
                    id=1,
                    current_node_id=DEPOT_ID,
                    current_position=(0.0, 0.0),
                    current_load=0,
                    trips=[
                        Trip(
                            stops=[
                                Stop(DEPOT_ID, 0),
                                Stop("T1", 0, is_transit=True),
                                Stop("A", 4),
                                Stop("T1", 0, is_transit=True),
                                Stop(DEPOT_ID, 0),
                            ],
                            distance=30.0,
                        )
                    ],
                ),
            ],
            total_system_distance=30.0,
            road_network=network,
            transit_nodes=[],
        )

        self.assertEqual(extract_vehicle_assignments(result)[1], [DeliveryTask("A", 4)])
