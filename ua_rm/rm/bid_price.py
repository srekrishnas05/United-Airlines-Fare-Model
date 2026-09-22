"""Bid price — opportunity cost of selling one more seat now."""
from __future__ import annotations

import numpy as np

from ua_rm.params import (
    PACING_RATIO_CLIP,
    SCARCITY_PREMIUM_PEAK,
    SCARCITY_TRIGGER_FRAC,
)
from ua_rm.rm.booking_curve import BookingCurve, pacing_ratio
from ua_rm.rm.inventory import CabinInventory


def compute_bid_price(
    inventory: CabinInventory,
    curve: BookingCurve,
    days_to_departure: int,
    wtp: float,
) -> float:
    ratio = pacing_ratio(
        inventory.seats_sold, inventory.total_seats, curve, days_to_departure
    )
    pacing_factor = float(np.clip(ratio, *PACING_RATIO_CLIP))

    scarcity_factor = 1.0
    trigger = SCARCITY_TRIGGER_FRAC * inventory.total_seats
    if inventory.seats_available < trigger and inventory.total_seats > 0:
        # Linearly ramp from 1.0 (at trigger) up to 1+SCARCITY_PREMIUM_PEAK (at 0 left)
        depletion = 1.0 - inventory.seats_available / trigger
        scarcity_factor = 1.0 + depletion * SCARCITY_PREMIUM_PEAK

    return wtp * pacing_factor * scarcity_factor
