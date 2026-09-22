"""Pricing engine — assembles multipliers into a WTP price per cabin.

Pure function: takes explicit parameters, no global state.
"""
from __future__ import annotations

from datetime import date

import numpy as np

from ua_rm.config.aircraft import Aircraft
from ua_rm.config.routes import Route
from ua_rm.params import WTP_NOISE_SIGMA
from ua_rm.pricing.base_fare import base_fare
from ua_rm.pricing.holiday_boost import holiday_boost
from ua_rm.pricing.scarcity import scarcity_multiplier
from ua_rm.pricing.seasonality import seasonality
from ua_rm.pricing.tod import tod_multiplier
from ua_rm.pricing.ttd import ttd_multiplier


def compute_wtp(
    route: Route,
    aircraft: Aircraft,
    cabin: str,
    departure_date: date,
    query_date: date,
    add_noise: bool = True,
    rng: np.random.Generator | None = None,
) -> float:
    """Returns the modeled willingness-to-pay price for this cabin."""
    days_to_departure = (departure_date - query_date).days

    base = base_fare(route, cabin)
    s   = seasonality(route, departure_date, cabin)
    h   = holiday_boost(route, departure_date)
    t   = ttd_multiplier(days_to_departure, cabin)
    sc  = scarcity_multiplier(aircraft, cabin)
    tod = tod_multiplier(route, cabin)

    if add_noise:
        gen = rng if rng is not None else np.random.default_rng()
        noise = float(gen.lognormal(mean=0.0, sigma=WTP_NOISE_SIGMA))
    else:
        noise = 1.0

    return base * s * h * t * sc * tod * noise
