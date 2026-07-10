"""Testes de pathfinding com custo de aresta reutilizada."""

import unittest

from traveling_salesman_problem.problem.road_network import (
    RoadNetwork,
    canonical_edge,
    find_path_weighted,
    path_weighted_distance,
)


class WeightedPathfindingTests(unittest.TestCase):
    def setUp(self) -> None:
        # Short D—A—X (20); longer D—B—X (~28) still wins after A-edges are reused at ×1.75
        self.network = RoadNetwork(
            nodes={
                "D": (0.0, 0.0),
                "A": (10.0, 0.0),
                "B": (10.0, 10.0),
                "X": (20.0, 0.0),
            },
            edges=[("D", "A"), ("A", "X"), ("D", "B"), ("B", "X")],
            connection_radius=100.0,
        )

    def test_canonical_edge_order(self) -> None:
        self.assertEqual(canonical_edge("B", "A"), ("A", "B"))

    def test_empty_used_matches_unweighted_preference(self) -> None:
        path = find_path_weighted(self.network, "D", "X", reuse_penalty=1.75)
        self.assertEqual(path, ["D", "A", "X"])

    def test_reuse_prefers_alternate_route(self) -> None:
        used = {canonical_edge("D", "A"), canonical_edge("A", "X")}
        path = find_path_weighted(
            self.network, "X", "D", used_edges=used, reuse_penalty=1.75
        )
        self.assertEqual(path, ["X", "B", "D"])

    def test_single_path_still_reachable_with_reuse(self) -> None:
        line = RoadNetwork(
            nodes={"D": (0.0, 0.0), "X": (10.0, 0.0)},
            edges=[("D", "X")],
            connection_radius=20.0,
        )
        used = {canonical_edge("D", "X")}
        path = find_path_weighted(line, "D", "X", used_edges=used, reuse_penalty=1.75)
        self.assertEqual(path, ["D", "X"])
        cost = path_weighted_distance(line, path, used, 1.75)
        self.assertAlmostEqual(cost, 10.0 * 1.75)

    def test_mesh_segment_prefers_alternate_after_reuse(self) -> None:
        from traveling_salesman_problem.problem.delivery_mesh import (
            delivery_mesh_from_parts,
            delivery_segment_path,
        )

        mesh = delivery_mesh_from_parts(
            self.network,
            delivery_ids=["X"],
            transit_ids=["A", "B"],
        )
        # Remap: network uses D not DEPOT — rebuild with DEPOT id for mesh helpers
        network = RoadNetwork(
            nodes={
                "DEPOT": (0.0, 0.0),
                "A": (10.0, 0.0),
                "B": (10.0, 10.0),
                "X": (20.0, 0.0),
            },
            edges=[("DEPOT", "A"), ("A", "X"), ("DEPOT", "B"), ("B", "X")],
            connection_radius=100.0,
        )
        mesh = delivery_mesh_from_parts(
            network,
            delivery_ids=["X"],
            transit_ids=["A", "B"],
        )
        used = {canonical_edge("DEPOT", "A"), canonical_edge("A", "X")}
        path = delivery_segment_path(
            mesh,
            (20.0, 0.0),
            (0.0, 0.0),
            used_edges=used,
            reuse_penalty=1.75,
        )
        self.assertEqual(path, ["X", "B", "DEPOT"])


if __name__ == "__main__":
    unittest.main()
