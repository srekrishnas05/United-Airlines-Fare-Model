"""Gaussian demand windows around holidays."""
from __future__ import annotations

import math
from datetime import date, timedelta

from ua_rm.config.holidays import holidays_for_route
from ua_rm.config.routes import Route
from ua_rm.params import HOLIDAY_BASE_PEAK, HOLIDAY_GAUSSIAN_SIGMA_DAYS


def _days_to_nearest_holiday(d: date, route: Route) -> tuple[int, float]:
    """Returns (days_distance, strength) for the nearest holiday around d."""
    holidays = holidays_for_route(route.holiday_country)
    if not holidays:
        return (10_000, 1.0)
    best = (10_000, 1.0)
    for h in holidays:
        # Try the holiday in the year before, the same year, and the year after,
        # so a January departure can match a December holiday from the prior year.
        for year_offset in (-1, 0, 1):
            try:
                hd = date(d.year + year_offset, h.month, h.day)
            except ValueError:
                continue
            delta = abs((d - hd).days)
            if delta < best[0]:
                best = (delta, h.strength)
    return best


def holiday_boost(route: Route, departure_date: date) -> float:
    days, strength = _days_to_nearest_holiday(departure_date, route)
    sigma = HOLIDAY_GAUSSIAN_SIGMA_DAYS
    peak = HOLIDAY_BASE_PEAK * strength
    bump = peak * math.exp(-(days ** 2) / (2 * sigma * sigma))
    return 1.0 + bump
