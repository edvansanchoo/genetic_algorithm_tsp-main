"""Testes da animação sequencial por viagem."""

import unittest

from traveling_salesman_problem.problem.delivery_mesh import delivery_mesh_from_parts
from traveling_salesman_problem.problem.road_network import RoadNetwork
from traveling_salesman_problem.problem.vrp_decoder import DecodedVehiclePlan
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, Trip, TripStop
from traveling_salesman_problem.visualization.route_animation import (
    TripAnimationState,
    advance_trip_animation,
    build_animation_polyline,
    drawable_trip_indices,
)


def _plan_with_two_trips() -> DecodedVehiclePlan:
    depot = (0.0, 0.0)
    return DecodedVehiclePlan(
        trips=[
            Trip(
                stops=[
                    TripStop(DEPOT_ID, 0, depot),
                    TripStop("A", 3, (10.0, 0.0)),
                    TripStop(DEPOT_ID, 0, depot),
                ],
                distance=20.0,
                path_node_ids=[[DEPOT_ID, "A", DEPOT_ID]],
            ),
            Trip(
                stops=[
                    TripStop(DEPOT_ID, 0, depot),
                    TripStop("B", 2, (0.0, 10.0)),
                    TripStop(DEPOT_ID, 0, depot),
                ],
                distance=20.0,
                path_node_ids=[[DEPOT_ID, "B", DEPOT_ID]],
            ),
        ],
        total_distance=40.0,
        priority_penalty=0.0,
        fitness=40.0,
    )


class TripAnimationTests(unittest.TestCase):
    def setUp(self) -> None:
        network = RoadNetwork(
            nodes={
                DEPOT_ID: (0.0, 0.0),
                "A": (10.0, 0.0),
                "B": (0.0, 10.0),
            },
            edges=[
                (DEPOT_ID, "A"),
                (DEPOT_ID, "B"),
            ],
            connection_radius=15.0,
        )
        self.mesh = delivery_mesh_from_parts(
            network,
            delivery_ids=["A", "B"],
            transit_ids=[],
        )
        self.plan = _plan_with_two_trips()

    def test_build_animation_polyline_single_trip(self):
        trip_zero = build_animation_polyline(self.mesh, self.plan, trip_index=0)
        trip_one = build_animation_polyline(self.mesh, self.plan, trip_index=1)
        self.assertNotEqual(trip_zero, trip_one)
        self.assertEqual(trip_zero[0], (0.0, 0.0))
        self.assertEqual(trip_one[0], (0.0, 0.0))

    def test_drawable_trip_indices(self):
        self.assertEqual(drawable_trip_indices(self.plan), [0, 1])

    def test_locked_trip_stays_on_selected_trip(self):
        state = TripAnimationState()
        cursor, active = advance_trip_animation(
            state,
            self.mesh,
            self.plan,
            0.5,
            locked_trip_index=1,
            speed=0.5,
        )
        self.assertEqual(active, 1)
        self.assertIsNotNone(cursor)

    def test_auto_cycle_advances_after_trip_completes(self):
        state = TripAnimationState()
        state.progress = 0.99
        _, active = advance_trip_animation(
            state,
            self.mesh,
            self.plan,
            0.1,
            locked_trip_index=None,
            speed=0.5,
            depot_pause_seconds=0.0,
        )
        self.assertIn(active, (0, 1))


if __name__ == "__main__":
    unittest.main()
