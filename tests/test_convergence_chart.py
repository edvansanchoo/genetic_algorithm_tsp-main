import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.visualization.convergence_chart import draw_convergence_chart


class ConvergenceChartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_multi_series_does_not_raise(self):
        screen = pygame.Surface((450, 400))
        draw_convergence_chart(
            screen,
            [0, 1, 2],
            [[100.0, 90.0, 80.0], [120.0, 110.0, 100.0]],
            series_colors=VisualTheme.vehicle_route_colors,
            series_labels=["V1", "V2"],
        )

    def test_highlight_index_does_not_raise(self):
        screen = pygame.Surface((450, 400))
        draw_convergence_chart(
            screen,
            [0, 1, 2],
            [[100.0, 90.0, 80.0], [120.0, 110.0, 100.0]],
            series_colors=VisualTheme.vehicle_route_colors,
            series_labels=["V1", "V2"],
            highlight_index=0,
        )
