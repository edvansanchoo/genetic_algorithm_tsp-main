"""Testes de desenho da 2ª melhor rota."""

import unittest
from unittest.mock import MagicMock, patch

from traveling_salesman_problem.problem.vrp_decoder import DecodedVehiclePlan
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, Trip, TripStop
from traveling_salesman_problem.visualization.map_renderer import draw_runner_up_plan


class DrawRunnerUpPlanTests(unittest.TestCase):
    @patch("traveling_salesman_problem.visualization.map_renderer._draw_dashed_polyline")
    def test_draws_dashed_for_each_trip(self, mock_dashed) -> None:
        screen = MagicMock()
        mesh = MagicMock()
        mesh.network.nodes = {DEPOT_ID: (0.0, 0.0), "A": (10.0, 0.0)}
        trip = Trip(
            stops=[
                TripStop(node_id=DEPOT_ID, quantity=0, coordinate=(0.0, 0.0)),
                TripStop(node_id="A", quantity=1, coordinate=(10.0, 0.0)),
                TripStop(node_id=DEPOT_ID, quantity=0, coordinate=(0.0, 0.0)),
            ],
            distance=20.0,
            path_node_ids=[[DEPOT_ID, "A", DEPOT_ID]],
        )
        plan = DecodedVehiclePlan(
            trips=[trip],
            total_distance=20.0,
            priority_penalty=0.0,
            fitness=20.0,
        )
        draw_runner_up_plan(screen, mesh, plan)
        self.assertEqual(mock_dashed.call_count, 1)

    @patch("traveling_salesman_problem.visualization.map_renderer._draw_dashed_polyline")
    def test_draws_only_selected_trip(self, mock_dashed) -> None:
        screen = MagicMock()
        mesh = MagicMock()
        mesh.network.nodes = {DEPOT_ID: (0.0, 0.0), "A": (10.0, 0.0), "B": (0.0, 10.0)}
        trips = [
            Trip(
                stops=[
                    TripStop(node_id=DEPOT_ID, quantity=0, coordinate=(0.0, 0.0)),
                    TripStop(node_id="A", quantity=1, coordinate=(10.0, 0.0)),
                    TripStop(node_id=DEPOT_ID, quantity=0, coordinate=(0.0, 0.0)),
                ],
                distance=20.0,
                path_node_ids=[[DEPOT_ID, "A", DEPOT_ID]],
            ),
            Trip(
                stops=[
                    TripStop(node_id=DEPOT_ID, quantity=0, coordinate=(0.0, 0.0)),
                    TripStop(node_id="B", quantity=1, coordinate=(0.0, 10.0)),
                    TripStop(node_id=DEPOT_ID, quantity=0, coordinate=(0.0, 0.0)),
                ],
                distance=20.0,
                path_node_ids=[[DEPOT_ID, "B", DEPOT_ID]],
            ),
        ]
        plan = DecodedVehiclePlan(
            trips=trips,
            total_distance=40.0,
            priority_penalty=0.0,
            fitness=40.0,
        )
        draw_runner_up_plan(screen, mesh, plan, trip_index=1)
        self.assertEqual(mock_dashed.call_count, 1)


if __name__ == "__main__":
    unittest.main()
