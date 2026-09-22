"""Time-of-day preference adjustment.

V1 modeled this as a simple regional preference for outbound timing;
the simulator runs at day granularity so we collapse to a per-region,
per-cabin scalar that nudges WTP for popular timing windows.
"""
from __future__ import annotations

from ua_rm.config.routes import Route
from ua_rm.params import TOD_FACTOR_BY_REGION


def tod_multiplier(route: Route, cabin: str) -> float:
    base = TOD_FACTOR_BY_REGION.get(route.region, 1.0)
    # Business cabins get slightly more from popular timing
    if cabin == "J":
        return 1.0 + (base - 1.0) * 1.2
    if cabin == "W":
        return base
    return 1.0 + (base - 1.0) * 0.8
