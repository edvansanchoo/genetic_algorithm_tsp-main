import unittest

from delivery_simulation.fuel.models import MAX_FUEL, GasStation, RouteFuelReport
from delivery_simulation.fuel.simulation import travel_with_fuel
from delivery_simulation.models import DEPOT_ID
from delivery_simulation.road_network import build_road_network


class FuelModelTests(unittest.TestCase):
    def test_max_fuel_is_150(self):
        self.assertEqual(MAX_FUEL, 150.0)

    def test_gas_station_frozen(self):
        station = GasStation("F1", (10.0, 20.0))
        self.assertEqual(station.id, "F1")
        with self.assertRaises(Exception):
            station.id = "F2"  # type: ignore[misc]


class TravelWithFuelTests(unittest.TestCase):
    def test_direct_leg_consumes_distance(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (40.0, 0.0)}
        network = build_road_network(nodes, radius=50.0)
        result = travel_with_fuel(
            network, DEPOT_ID, "A", fuel=150.0, station_ids=set(), visited_stations=set(), blocked=set()
        )
        self.assertTrue(result.is_feasible)
        self.assertAlmostEqual(result.distance, 40.0)
        self.assertAlmostEqual(result.fuel_after, 110.0)
        self.assertEqual(result.stops, [])

    def test_detours_to_station_when_fuel_insufficient(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "F1": (50.0, 0.0),
            "A": (100.0, 0.0),
        }
        network = build_road_network(nodes, radius=55.0)
        result = travel_with_fuel(
            network,
            DEPOT_ID,
            "A",
            fuel=50.0,
            station_ids={"F1"},
            visited_stations=set(),
            blocked=set(),
        )
        self.assertTrue(result.is_feasible)
        self.assertEqual(len(result.stops), 1)
        self.assertEqual(result.stops[0].station_id, "F1")
        self.assertAlmostEqual(result.stops[0].fuel_on_departure, 150.0)
        self.assertIn("F1", result.visited_stations)
        self.assertAlmostEqual(result.fuel_after, 100.0)

    def test_dry_out_when_no_viable_station(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (100.0, 0.0)}
        network = build_road_network(nodes, radius=150.0)
        result = travel_with_fuel(
            network, DEPOT_ID, "A", fuel=10.0, station_ids=set(), visited_stations=set(), blocked=set()
        )
        self.assertFalse(result.is_feasible)

    def test_does_not_revisit_station(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "F1": (50.0, 0.0),
            "A": (100.0, 0.0),
        }
        network = build_road_network(nodes, radius=55.0)
        result = travel_with_fuel(
            network,
            DEPOT_ID,
            "A",
            fuel=50.0,
            station_ids={"F1"},
            visited_stations={"F1"},
            blocked=set(),
        )
        self.assertFalse(result.is_feasible)
