import unittest

from delivery_simulation.distance import euclidean


class EuclideanDistanceTests(unittest.TestCase):
    def test_horizontal_segment(self):
        self.assertAlmostEqual(euclidean((0, 0), (3, 0)), 3.0)

    def test_diagonal_3_4_5(self):
        self.assertAlmostEqual(euclidean((0, 0), (3, 4)), 5.0)

    def test_same_point_is_zero(self):
        self.assertAlmostEqual(euclidean((100, 200), (100, 200)), 0.0)
