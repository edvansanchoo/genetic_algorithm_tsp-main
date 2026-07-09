import math
import random
import unittest

from delivery_simulation.point_generator import generate_depot_and_points


class PointGeneratorTests(unittest.TestCase):
    def test_returns_depot_and_requested_point_count(self):
        depot, points = generate_depot_and_points(
            point_count=3,
            map_min_x=100,
            map_min_y=100,
            map_max_x=500,
            map_max_y=400,
            rng=random.Random(7),
        )
        self.assertEqual(len(points), 3)
        self.assertEqual([point_id for point_id, _ in points], ["A", "B", "C"])
        self.assertEqual(len(depot), 2)

    def test_coordinates_inside_map_bounds(self):
        depot, points = generate_depot_and_points(
            point_count=2,
            map_min_x=100,
            map_min_y=100,
            map_max_x=500,
            map_max_y=400,
            rng=random.Random(3),
        )
        all_coords = [depot] + [coord for _, coord in points]
        for x, y in all_coords:
            self.assertGreaterEqual(x, 100)
            self.assertLessEqual(x, 500)
            self.assertGreaterEqual(y, 100)
            self.assertLessEqual(y, 400)

    def test_minimum_separation_between_all_points(self):
        depot, points = generate_depot_and_points(
            point_count=3,
            map_min_x=0,
            map_min_y=0,
            map_max_x=1000,
            map_max_y=1000,
            min_separation=30.0,
            rng=random.Random(11),
        )
        coords = [depot] + [coord for _, coord in points]
        for index_a, coord_a in enumerate(coords):
            for coord_b in coords[index_a + 1:]:
                distance = math.hypot(coord_b[0] - coord_a[0], coord_b[1] - coord_a[1])
                self.assertGreaterEqual(distance, 30.0)
