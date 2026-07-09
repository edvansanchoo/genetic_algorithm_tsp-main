"""Distribuição aleatória de itens entre pontos de entrega."""

import random
from typing import Dict, Optional

from delivery_simulation.models import POINT_IDS


def distribute_items(
    total_items: int,
    point_count: int,
    rng: Optional[random.Random] = None,
) -> Dict[str, int]:
    if point_count < 1 or point_count > len(POINT_IDS):
        raise ValueError(f"point_count deve estar entre 1 e {len(POINT_IDS)}")

    random_source = rng or random.Random()
    point_ids = POINT_IDS[:point_count]
    orders = {point_id: 0 for point_id in point_ids}

    for _ in range(total_items):
        chosen_id = random_source.choice(point_ids)
        orders[chosen_id] += 1

    return orders
