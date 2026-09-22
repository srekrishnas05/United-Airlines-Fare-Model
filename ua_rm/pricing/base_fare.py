"""Distance-anchored base fare with competition and J yield-tier adjustments."""
from __future__ import annotations

from ua_rm.config.routes import Route
from ua_rm.params import (
    COMPETITION_FACTOR,
    DISTANCE_EXPONENT,
    FARE_PER_KM,
    J_YIELD_TIER_FACTOR,
)


def base_fare(route: Route, cabin: str) -> float:
    distance_base = FARE_PER_KM[cabin] * (route.distance_km ** DISTANCE_EXPONENT)
    comp = COMPETITION_FACTOR[route.competition_level]
    jyt = J_YIELD_TIER_FACTOR[cabin][route.j_yield_tier]
    return distance_base * comp * jyt
