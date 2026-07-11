"""Testes da legenda contextual do mapa."""

import unittest

from traveling_salesman_problem.visualization.application_layout import _build_legend_items


class MapLegendTests(unittest.TestCase):
    def test_default_startup_legend_is_compact(self) -> None:
        labels = [item.label for item in _build_legend_items(False, 1, None, False)]
        self.assertIn("Depósito", labels)
        self.assertIn("Rota — viagem 1", labels)
        self.assertNotIn("Aresta da malha", labels)
        self.assertNotIn("2ª melhor (foco)", labels)

    def test_mesh_items_only_when_enabled(self) -> None:
        hidden = [item.label for item in _build_legend_items(False, 1, None, False)]
        visible = [item.label for item in _build_legend_items(True, 1, None, False)]
        self.assertNotIn("Aresta da malha", hidden)
        self.assertIn("Aresta da malha", visible)

    def test_multi_vehicle_lists_each_route(self) -> None:
        labels = [item.label for item in _build_legend_items(False, 3, None, False)]
        self.assertIn("V1 rota", labels)
        self.assertIn("V2 rota", labels)
        self.assertIn("V3 rota", labels)

    def test_focus_mode_adds_runner_up_when_available(self) -> None:
        labels = [item.label for item in _build_legend_items(False, 2, 0, True, trip_auto_cycle=True)]
        self.assertIn("V1 rota", labels)
        self.assertNotIn("V2 rota", labels)
        self.assertIn("Outros veículos (foco)", labels)
        self.assertIn("2ª melhor — viagem ativa", labels)
        self.assertIn("Viagem ativa (auto)", labels)
        self.assertIn("Animação (foco)", labels)

    def test_locked_trip_shows_fixed_label(self) -> None:
        labels = [item.label for item in _build_legend_items(False, 2, 0, False, focus_trip_index=1)]
        self.assertIn("Viagem 2 (fixa)", labels)


if __name__ == "__main__":
    unittest.main()
