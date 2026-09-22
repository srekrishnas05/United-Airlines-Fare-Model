"""Time-to-departure urgency curves per cabin.

Logistic curves: as days_to_departure shrinks, urgency multiplier grows.
Business cabin starts climbing earlier and reaches a higher ceiling.
"""
from __future__ import annotations

import math

from ua_rm.params import TTD_PARAMS


def ttd_multiplier(days_to_departure: int, cabin: str) -> float:
    p = TTD_PARAMS[cabin]
    urgency = p["L"] / (1.0 + math.exp(-p["k"] * (p["x0"] - days_to_departure)))
    return max(urgency, p["floor"])
