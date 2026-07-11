"""Testes de retorno ao depósito com rota diferente da ida."""

import unittest

from traveling_salesman_problem.problem.delivery_mesh import (
    delivery_mesh_from_parts,
    delivery_segment_path,
)
from traveling_salesman_problem.problem.road_network import (
    RoadNetwork,
    canonical_edge,
    find_path_weighted,
)
from traveling_salesman_problem.problem.vrp_decoder import (
    _edges_from_path,
    decode_vehicle_permutation,
)
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, DeliveryToken


def _diamond_network():
    return RoadNetwork(
        nodes={
            DEPOT_ID: (0.0, 0.0),
            "A": (10.0, 0.0),
            "B": (10.0, 10.0),
            "X": (20.0, 0.0),
        },
        edges=[
            (DEPOT_ID, "A"),
            ("A", "X"),
            (DEPOT_ID, "B"),
            ("B", "X"),
        ],
        connection_radius=100.0,
    )


def _two_corridor_network():
    return RoadNetwork(
        nodes={
            DEPOT_ID: (0.0, 0.0),
            "A": (10.0, 0.0),
            "B": (10.0, 10.0),
            "C": (-10.0, 0.0),
            "X": (20.0, 0.0),
            "E": (25.0, 5.0),
            "F": (15.0, 20.0),
        },
        edges=[
            (DEPOT_ID, "A"),
            ("A", "X"),
            (DEPOT_ID, "B"),
            ("B", "X"),
            (DEPOT_ID, "C"),
            ("C", "X"),
            ("X", "E"),
            ("E", "F"),
            ("F", DEPOT_ID),
        ],
        connection_radius=100.0,
    )


def _trip_edges(trip) -> set:
    edges: set = set()
    for path in trip.path_node_ids:
        edges.update(_edges_from_path(path))
    return edges


class ForbiddenEdgePathfindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.network = _diamond_network()

    def test_return_uses_alternate_when_outbound_edges_forbidden(self) -> None:
        outbound = {canonical_edge(DEPOT_ID, "A"), canonical_edge("A", "X")}
        path = find_path_weighted(
            self.network, "X", DEPOT_ID, forbidden_edges=outbound
        )
        self.assertEqual(path, ["X", "B", DEPOT_ID])

    def test_forbidden_empty_matches_shortest(self) -> None:
        path = find_path_weighted(self.network, DEPOT_ID, "X")
        self.assertEqual(path, [DEPOT_ID, "A", "X"])


class MeshForbiddenSegmentTests(unittest.TestCase):
    def test_mesh_segment_respects_forbidden_edges(self) -> None:
        mesh = delivery_mesh_from_parts(
            _diamond_network(),
            delivery_ids=["X"],
            transit_ids=["A", "B"],
        )
        forbidden = {canonical_edge(DEPOT_ID, "A"), canonical_edge("A", "X")}
        path = delivery_segment_path(
            mesh,
            (20.0, 0.0),
            (0.0, 0.0),
            forbidden_edges=forbidden,
        )
        self.assertEqual(path, ["X", "B", DEPOT_ID])


class DecoderReturnDiversificationTests(unittest.TestCase):
    def test_decoder_return_differs_from_outbound_on_diamond(self) -> None:
        mesh = delivery_mesh_from_parts(
            _diamond_network(),
            delivery_ids=["X"],
            transit_ids=["A", "B"],
        )
        tokens = [DeliveryToken("X", 1, priority=5)]
        plan = decode_vehicle_permutation(
            tokens,
            list(tokens),
            (0.0, 0.0),
            mesh,
            capacity=10,
        )
        trip = plan.trips[0]
        self.assertEqual(trip.path_node_ids[0], [DEPOT_ID, "A", "X"])
        self.assertEqual(trip.path_node_ids[1], ["X", "B", DEPOT_ID])

    def test_decoder_single_edge_return_requires_reuse(self) -> None:
        network = RoadNetwork(
            nodes={DEPOT_ID: (0.0, 0.0), "X": (10.0, 0.0)},
            edges=[(DEPOT_ID, "X")],
            connection_radius=20.0,
        )
        mesh = delivery_mesh_from_parts(network, delivery_ids=["X"], transit_ids=[])
        tokens = [DeliveryToken("X", 1, priority=5)]
        plan = decode_vehicle_permutation(
            tokens,
            list(tokens),
            (0.0, 0.0),
            mesh,
            capacity=10,
        )
        self.assertEqual(plan.fitness, float("inf"))


class InterTripPlanEdgesTests(unittest.TestCase):
    def test_second_trip_avoids_first_trip_edges(self) -> None:
        mesh = delivery_mesh_from_parts(
            _two_corridor_network(),
            delivery_ids=["A", "X"],
            transit_ids=["B", "C", "E", "F"],
        )
        tokens = [
            DeliveryToken("A", 6, priority=5),
            DeliveryToken("X", 6, priority=5),
        ]
        plan = decode_vehicle_permutation(
            tokens,
            list(tokens),
            (0.0, 0.0),
            mesh,
            capacity=10,
        )
        self.assertEqual(len(plan.trips), 2)
        trip0_edges = _trip_edges(plan.trips[0])
        trip1_outbound = _edges_from_path(plan.trips[1].path_node_ids[0])
        self.assertFalse(trip0_edges & trip1_outbound)
        self.assertEqual(plan.trips[1].path_node_ids[0], [DEPOT_ID, "C", "X"])
        self.assertEqual(
            plan.trips[1].path_node_ids[1], ["X", "E", "F", DEPOT_ID]
        )


if __name__ == "__main__":
    unittest.main()
