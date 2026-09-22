"""EMSR-b protection level computation.

Determines how many seats to protect for higher-yield demand. The
algorithm walks down the fare ladder; at each lower class, it computes
how many seats should be reserved for the *aggregated* higher classes
based on a normal approximation of remaining demand.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ua_rm.config.fare_classes import FareClass, fares_for_cabin
from ua_rm.params import EMSR_DEMAND_COV
from ua_rm.rm.booking_curve import BookingCurve
from ua_rm.rm.inventory import CabinInventory


@dataclass
class ClassDemandForecast:
    fare_class: str
    mean: float        # expected remaining bookings
    std: float
    fare: float        # expected revenue per seat


def _normal_inverse_cdf(p: float) -> float:
    """Beasley-Springer-Moro approximation of the inverse normal CDF."""
    p = min(max(p, 1e-9), 1 - 1e-9)
    a = [-3.969683028665376e+01,  2.209460984245205e+02,
         -2.759285104469687e+02,  1.383577518672690e+02,
         -3.066479806614716e+01,  2.506628277459239e+00]
    b = [-5.447609879822406e+01,  1.615858368580409e+02,
         -1.556989798598866e+02,  6.680131188771972e+01,
         -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
          4.374664141464968e+00,  2.938163982698783e+00]
    d = [ 7.784695709041462e-03,  3.224671290700398e-01,
          2.445134137142996e+00,  3.754408661907416e+00]
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
               ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
                ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r + a[1])*r + a[2])*r + a[3])*r + a[4])*r + a[5]) * q / \
           (((((b[0]*r + b[1])*r + b[2])*r + b[3])*r + b[4])*r + 1)


def _forecast_remaining_demand(
    cabin: str,
    inventory: CabinInventory,
    curve: BookingCurve,
    days_to_departure: int,
    cabin_wtp: float,
) -> list[ClassDemandForecast]:
    """Build a fare→(mean, std, expected fare) forecast over the remaining window."""
    fares = fares_for_cabin(cabin)
    expected_full = curve.fraction_at(0) * inventory.total_seats
    expected_now = curve.fraction_at(days_to_departure) * inventory.total_seats
    remaining = max(0.0, expected_full - expected_now)

    # Higher-yield classes get a smaller share of remaining demand than
    # lower-yield (a simple monotone weight). Sum of weights = 1.
    n = len(fares)
    weights = []
    for i, _ in enumerate(fares):
        # weight grows toward the bottom of the ladder
        weights.append(1.0 + 0.6 * (i / max(n - 1, 1)))
    total_w = sum(weights)
    weights = [w / total_w for w in weights]

    forecasts: list[ClassDemandForecast] = []
    for fare, w in zip(fares, weights):
        mean = remaining * w
        std = max(1.0, mean * EMSR_DEMAND_COV)
        forecasts.append(ClassDemandForecast(
            fare_class=fare.code,
            mean=mean,
            std=std,
            fare=cabin_wtp * fare.wtp_ratio,
        ))
    return forecasts


def compute_protection_levels(
    cabin: str,
    inventory: CabinInventory,
    curve: BookingCurve,
    days_to_departure: int,
    cabin_wtp: float,
) -> dict[str, int]:
    """Returns {fare_class: seats protected for this class AND above}."""
    forecasts = _forecast_remaining_demand(
        cabin, inventory, curve, days_to_departure, cabin_wtp
    )

    capacity = max(0, inventory.seats_available)
    protections: dict[str, int] = {}

    # EMSR-b: for each lower class i, aggregate higher classes 1..i-1
    # into a single "protect this much" decision.
    for i in range(1, len(forecasts)):
        higher = forecasts[:i]
        lower_fare = forecasts[i].fare
        if lower_fare <= 0 or not higher:
            protections[forecasts[i].fare_class] = 0
            continue
        # Aggregated mean and variance for higher-yield demand
        agg_mean = sum(f.mean for f in higher)
        agg_var = sum(f.std ** 2 for f in higher)
        agg_std = math.sqrt(agg_var) if agg_var > 0 else 1.0
        # Weighted average yield of the higher classes
        agg_fare = (
            sum(f.mean * f.fare for f in higher) / agg_mean
            if agg_mean > 0 else lower_fare
        )
        # Critical fractile: protect until P(demand > x) = lower_fare / agg_fare
        crit = 1.0 - (lower_fare / agg_fare)
        if crit <= 0:
            level = 0
        else:
            z = _normal_inverse_cdf(crit)
            level = int(round(agg_mean + z * agg_std))
        level = max(0, min(level, capacity))
        protections[forecasts[i].fare_class] = level

    # Top class doesn't need protection above it
    protections[forecasts[0].fare_class] = 0
    return protections


def total_protection(protections: dict[str, int]) -> int:
    """Total seats reserved for all higher-yield classes — equals the largest level."""
    if not protections:
        return 0
    return max(protections.values())
