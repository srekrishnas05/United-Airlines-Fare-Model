"""Expected booking curves and pacing computation.

Each cabin has an S-curve giving the *cumulative* fraction of seats
expected to be sold by N days before departure. The simulator compares
actual sales to this curve and uses the deviation to drive bid price.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ua_rm.config.routes import Route
from ua_rm.params import BOOKING_CURVE_PARAMS


@dataclass
class BookingCurve:
    cabin: str
    expected_pct_sold: dict[int, float] = field(default_factory=dict)

    def fraction_at(self, days_out: int) -> float:
        if days_out in self.expected_pct_sold:
            return self.expected_pct_sold[days_out]
        if not self.expected_pct_sold:
            return 0.0
        # Nearest-key lookup for safety if asked outside built window.
        keys = sorted(self.expected_pct_sold.keys())
        if days_out <= keys[0]:
            return self.expected_pct_sold[keys[0]]
        if days_out >= keys[-1]:
            return self.expected_pct_sold[keys[-1]]
        return self.expected_pct_sold[min(keys, key=lambda k: abs(k - days_out))]


def _logistic(days_out: int, k: float, x0: float) -> float:
    """Cumulative logistic, sold fraction increases as days_out shrinks."""
    return 1.0 / (1.0 + math.exp(k * (days_out - x0)))


def build_booking_curve(
    cabin: str, route: Route, window_days: int
) -> BookingCurve:
    p = BOOKING_CURVE_PARAMS[cabin]
    # Profile shifts: leisure-heavy routes pull the Y curve earlier; business-heavy
    # routes push it later (more last-minute bookings).
    x0 = p["x0"]
    if cabin == "Y":
        if route.demand_profile == "vfr_heavy":
            x0 += 15
        elif route.demand_profile == "business_heavy":
            x0 -= 10
    elif cabin == "J":
        if route.demand_profile == "business_heavy":
            x0 -= 5
    points: dict[int, float] = {}
    for days_out in range(0, window_days + 1):
        frac = _logistic(days_out, p["k"], x0)
        # Floor: tiny baseline so we don't divide by zero in pacing math.
        frac = max(p["floor_pct"] * (days_out == window_days), frac)
        points[days_out] = min(1.0, frac)
    return BookingCurve(cabin=cabin, expected_pct_sold=points)


def build_booking_curves(
    route: Route, window_days: int
) -> dict[str, BookingCurve]:
    return {
        cabin: build_booking_curve(cabin, route, window_days)
        for cabin in ("J", "W", "Y")
    }


def pacing_ratio(
    seats_sold: int, total_seats: int, curve: BookingCurve, days_out: int
) -> float:
    """Actual fraction sold ÷ expected fraction sold. 1.0 = on pace."""
    if total_seats <= 0:
        return 1.0
    actual = seats_sold / total_seats
    expected = curve.fraction_at(days_out)
    if expected <= 1e-6:
        # Very early in the window — treat as on pace if no sales yet
        return 1.0 if actual <= 1e-6 else 1.5
    return actual / expected
