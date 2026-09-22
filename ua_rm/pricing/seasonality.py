"""Per-cabin seasonality multiplier.

Y always feels the full swing; J is partially insulated by
route.j_seasonality_sensitivity; W sits between them.
"""
from __future__ import annotations

from datetime import date

from ua_rm.config.routes import Route
from ua_rm.params import SEASONALITY_TABLE


def seasonality(route: Route, departure_date: date, cabin: str) -> float:
    table = SEASONALITY_TABLE.get(route.region)
    if table is None:
        return 1.0
    base = table[departure_date.month]

    if cabin == "J":
        sensitivity = route.j_seasonality_sensitivity
    elif cabin == "W":
        sensitivity = min(route.j_seasonality_sensitivity + 0.3, 1.0)
    else:
        sensitivity = 1.0

    return 1.0 + (base - 1.0) * sensitivity
