"""Seat-supply pressure based on aircraft cabin density.

Smaller cabins push price up (limited supply); larger cabins push price
down (plenty of capacity). This is *aircraft-driven* scarcity — separate
from the dynamic remaining-inventory scarcity bump applied in the bid
price layer.
"""
from __future__ import annotations

from ua_rm.config.aircraft import Aircraft
from ua_rm.params import SCARCITY_REFERENCE_SEATS, SCARCITY_SLOPE


def scarcity_multiplier(aircraft: Aircraft, cabin: str) -> float:
    seats = aircraft.seats_for_cabin(cabin)
    ref = SCARCITY_REFERENCE_SEATS[cabin]
    slope = SCARCITY_SLOPE[cabin]
    if ref <= 0:
        return 1.0
    deviation = (ref - seats) / ref   # >0 if smaller than reference
    return max(0.7, min(1.5, 1.0 + slope * deviation))
