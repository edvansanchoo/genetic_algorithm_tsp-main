import unittest

from delivery_simulation.fuel.models import MAX_FUEL, GasStation, RouteFuelReport


class FuelModelTests(unittest.TestCase):
    def test_max_fuel_is_150(self):
        self.assertEqual(MAX_FUEL, 150.0)

    def test_gas_station_frozen(self):
        station = GasStation("F1", (10.0, 20.0))
        self.assertEqual(station.id, "F1")
        with self.assertRaises(Exception):
            station.id = "F2"  # type: ignore[misc]
