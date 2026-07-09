import random
import unittest

from delivery_simulation.models import VALID_TOTAL_ITEMS
from delivery_simulation.order_generator import distribute_items


class OrderGeneratorTests(unittest.TestCase):
    def test_sum_equals_total_for_all_valid_totals(self):
        for total in VALID_TOTAL_ITEMS:
            for point_count in (1, 2, 3):
                with self.subTest(total=total, point_count=point_count):
                    orders = distribute_items(total, point_count, rng=random.Random(42))
                    self.assertEqual(len(orders), point_count)
                    self.assertEqual(sum(orders.values()), total)
                    self.assertTrue(all(value >= 0 for value in orders.values()))

    def test_zero_items_allowed_on_some_points(self):
        orders = distribute_items(2, 3, rng=random.Random(0))
        self.assertEqual(sum(orders.values()), 2)

    def test_reproducible_with_seed(self):
        first = distribute_items(14, 3, rng=random.Random(99))
        second = distribute_items(14, 3, rng=random.Random(99))
        self.assertEqual(first, second)

    def test_single_point_gets_all_items(self):
        orders = distribute_items(8, 1, rng=random.Random(1))
        self.assertEqual(orders, {"A": 8})
