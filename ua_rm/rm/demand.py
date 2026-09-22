"""Stochastic demand: leisure + business segments + group + award streams.

Each time step the simulator calls `simulate_arrivals` to draw individual
arrivals, plus `maybe_group_event` and `maybe_award_arrivals` for the
lumpy / fixed-rate streams.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ua_rm.config.routes import Route
from ua_rm.params import (
    AVG_AWARDS_PER_MONTH,
    AWARD_FARE_CLASS,
    AWARD_REDEMPTION_VALUE_USD,
    CABIN_PREFERENCE,
    DEMAND_PEAK_DAYS_OUT,
    DEMAND_RATES,
    DEMAND_WINDOW_SIGMA,
    GROUP_DAILY_PROBABILITY,
    GROUP_DISCOUNT,
    GROUP_FARE_CLASSES,
    GROUP_PARTIAL_FILL_PROB,
    GROUP_SIZE_LAMBDA,
    GROUP_SIZE_MAX,
    GROUP_SIZE_MIN,
    PRICE_ELASTICITY,
)


@dataclass
class DemandSegment:
    name: str
    cabin_preference: dict[str, float]
    base_daily_rate: float
    peak_days_out: int
    sigma_days: float
    price_elasticity: float


@dataclass
class PassengerArrival:
    segment: str
    cabin: str           # preferred cabin
    wtp_factor: float    # multiplier on the cabin's WTP that this passenger will pay


@dataclass
class GroupBookingEvent:
    days_out: int
    cabin: str
    size: int
    fare_class: str
    discount_factor: float


@dataclass
class AwardArrival:
    cabin: str
    fare_class: str
    redemption_value: float


def build_demand_segments(route: Route) -> list[DemandSegment]:
    rates = DEMAND_RATES[route.demand_profile]
    return [
        DemandSegment(
            name="leisure",
            cabin_preference=CABIN_PREFERENCE["leisure"],
            base_daily_rate=rates["leisure"],
            peak_days_out=DEMAND_PEAK_DAYS_OUT["leisure"],
            sigma_days=DEMAND_WINDOW_SIGMA["leisure"],
            price_elasticity=PRICE_ELASTICITY["leisure"],
        ),
        DemandSegment(
            name="business",
            cabin_preference=CABIN_PREFERENCE["business"],
            base_daily_rate=rates["business"],
            peak_days_out=DEMAND_PEAK_DAYS_OUT["business"],
            sigma_days=DEMAND_WINDOW_SIGMA["business"],
            price_elasticity=PRICE_ELASTICITY["business"],
        ),
    ]


def _gaussian_shape(days_out: int, peak: int, sigma: float) -> float:
    """Returns a [0, 1] shape factor for the Poisson rate that day."""
    return math.exp(-((days_out - peak) ** 2) / (2 * sigma * sigma))


def expected_segment_rate(segment: DemandSegment, days_out: int) -> float:
    """Effective Poisson lambda for this segment at this point in the window."""
    return segment.base_daily_rate * _gaussian_shape(
        days_out, segment.peak_days_out, segment.sigma_days
    )


def _sample_cabin_preference(
    pref: dict[str, float], rng: np.random.Generator
) -> str:
    cabins = list(pref.keys())
    probs = np.array([pref[c] for c in cabins], dtype=float)
    probs = probs / probs.sum()
    return str(rng.choice(cabins, p=probs))


def _sample_wtp_factor(elasticity: float, rng: np.random.Generator) -> float:
    """How much WTP the passenger has, expressed as a factor of cabin WTP.

    Inelastic passengers cluster near 1.0 (or above). Elastic passengers
    have a wide spread, often well below the modeled WTP.
    """
    sigma = 0.05 + 0.45 * elasticity     # elastic → wider spread
    mu = -0.5 * sigma * sigma            # keep median ≈ 1.0
    return float(rng.lognormal(mean=mu, sigma=sigma))


def simulate_arrivals(
    segments: list[DemandSegment],
    days_out: int,
    time_step_days: int,
    rng: np.random.Generator,
) -> list[PassengerArrival]:
    """Draws Poisson arrivals from each segment for this time step."""
    arrivals: list[PassengerArrival] = []
    for seg in segments:
        rate = expected_segment_rate(seg, days_out) * time_step_days
        if rate <= 0:
            continue
        n = int(rng.poisson(rate))
        for _ in range(n):
            cabin = _sample_cabin_preference(seg.cabin_preference, rng)
            wtp_factor = _sample_wtp_factor(seg.price_elasticity, rng)
            arrivals.append(PassengerArrival(
                segment=seg.name, cabin=cabin, wtp_factor=wtp_factor
            ))
    return arrivals


def maybe_group_event(
    route: Route, days_out: int, rng: np.random.Generator
) -> GroupBookingEvent | None:
    """Bernoulli draw for a group booking event landing this day."""
    p = GROUP_DAILY_PROBABILITY[route.demand_profile]
    if rng.random() >= p:
        return None
    # Almost always Y, occasionally W
    cabin = "Y" if rng.random() < 0.9 else "W"
    raw = int(rng.poisson(GROUP_SIZE_LAMBDA))
    size = max(GROUP_SIZE_MIN, min(GROUP_SIZE_MAX, raw))
    fare_class = str(rng.choice(GROUP_FARE_CLASSES[cabin]))
    return GroupBookingEvent(
        days_out=days_out,
        cabin=cabin,
        size=size,
        fare_class=fare_class,
        discount_factor=GROUP_DISCOUNT,
    )


def maybe_award_arrivals(
    days_out: int,
    time_step_days: int,
    pacing_ratio: float,
    release_threshold: float,
    rng: np.random.Generator,
) -> list[AwardArrival]:
    """Award seats only release when the flight isn't pacing ahead."""
    if pacing_ratio >= release_threshold:
        return []
    arrivals: list[AwardArrival] = []
    for cabin in ("J", "W", "Y"):
        rate = (AVG_AWARDS_PER_MONTH[cabin] / 30.0) * time_step_days
        n = int(rng.poisson(rate))
        for _ in range(n):
            arrivals.append(AwardArrival(
                cabin=cabin,
                fare_class=AWARD_FARE_CLASS[cabin],
                redemption_value=AWARD_REDEMPTION_VALUE_USD[cabin],
            ))
    return arrivals
