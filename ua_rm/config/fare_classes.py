"""Fare class ladder.

Real airline fare classes map to cabins and have a hierarchy. Higher
classes are more expensive and protected longer. The fare controller
opens/closes these classes based on bid price at each time step.
"""
from __future__ import annotations

from dataclasses import dataclass


# Ordered from highest yield to lowest within each cabin
BUSINESS_CLASSES: list[str] = ["J", "C", "D", "Z", "P"]
PREMIUM_ECONOMY_CLASSES: list[str] = ["O", "A", "R"]
ECONOMY_CLASSES: list[str] = [
    "Y", "B", "M", "E", "U", "H", "Q", "V", "W", "S", "T", "L", "K"
]


@dataclass(frozen=True)
class FareClass:
    code: str
    cabin: str       # "J" | "W" | "Y"
    rank: int        # 1 = highest yield in cabin, N = lowest
    wtp_ratio: float # threshold = wtp * wtp_ratio


def _ladder(codes: list[str], cabin: str, top: float, bottom: float) -> list[FareClass]:
    """Build a fare class list with wtp_ratio linearly stepping top → bottom."""
    n = len(codes)
    if n == 1:
        ratios = [top]
    else:
        step = (top - bottom) / (n - 1)
        ratios = [top - i * step for i in range(n)]
    return [
        FareClass(code=code, cabin=cabin, rank=i + 1, wtp_ratio=ratios[i])
        for i, code in enumerate(codes)
    ]


# Top class threshold near 1.0 means it stays open under almost any bid price
# (only closes when bid_price exceeds nearly the full WTP). Bottom threshold
# is small — these classes close as soon as bid price climbs even a little.
BUSINESS_FARES: list[FareClass] = _ladder(BUSINESS_CLASSES, "J", top=0.98, bottom=0.45)
PE_FARES: list[FareClass]       = _ladder(PREMIUM_ECONOMY_CLASSES, "W", top=0.97, bottom=0.55)
ECONOMY_FARES: list[FareClass]  = _ladder(ECONOMY_CLASSES, "Y", top=0.96, bottom=0.30)


ALL_FARES: list[FareClass] = BUSINESS_FARES + PE_FARES + ECONOMY_FARES
FARES_BY_CODE: dict[str, FareClass] = {f.code: f for f in ALL_FARES}
FARES_BY_CABIN: dict[str, list[FareClass]] = {
    "J": BUSINESS_FARES,
    "W": PE_FARES,
    "Y": ECONOMY_FARES,
}


def fares_for_cabin(cabin: str) -> list[FareClass]:
    if cabin not in FARES_BY_CABIN:
        raise ValueError(f"Unknown cabin: {cabin}")
    return FARES_BY_CABIN[cabin]
