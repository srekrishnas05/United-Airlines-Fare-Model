"""Open/close fare classes based on the cabin bid price."""
from __future__ import annotations

from dataclasses import dataclass

from ua_rm.config.fare_classes import FareClass, fares_for_cabin
from ua_rm.rm.inventory import CabinInventory


@dataclass(frozen=True)
class FareClassState:
    code: str
    cabin: str
    is_open: bool
    threshold_price: float
    fare: float


def update_fare_classes(
    cabin: str,
    cabin_wtp: float,
    bid_price: float,
    inventory: CabinInventory,
) -> list[FareClassState]:
    """Returns ordered (highest rank first) state for every class in the cabin.

    Logic:
      - For each class, compute threshold = wtp * wtp_ratio
      - If bid_price >= threshold, close this class and all lower classes
      - If no seats are bookable, force close everything regardless
    """
    fares = fares_for_cabin(cabin)
    states: list[FareClassState] = []
    closed_below = False
    bookable = inventory.bookable_seats

    for fc in fares:
        threshold = cabin_wtp * fc.wtp_ratio
        fare_price = threshold  # the price a passenger would pay for this bucket
        if bookable <= 0:
            is_open = False
        elif closed_below:
            is_open = False
        elif bid_price >= threshold:
            is_open = False
            closed_below = True
        else:
            is_open = True
        states.append(FareClassState(
            code=fc.code,
            cabin=cabin,
            is_open=is_open,
            threshold_price=threshold,
            fare=fare_price,
        ))
    return states


def lowest_open_class(
    states: list[FareClassState], max_fare_factor: float
) -> FareClassState | None:
    """The cheapest open class with fare ≤ max_fare_factor * highest open fare.

    Used to assign an arriving passenger to a fare class they can pay.
    """
    open_states = [s for s in states if s.is_open]
    if not open_states:
        return None
    # Find lowest open class affordable to the passenger
    affordable = [s for s in open_states if s.fare <= max_fare_factor]
    if not affordable:
        return None
    # Pick the *lowest yield* (cheapest) class still open and affordable —
    # which is the last in rank order.
    return min(affordable, key=lambda s: s.fare)


def highest_open_class(states: list[FareClassState]) -> FareClassState | None:
    open_states = [s for s in states if s.is_open]
    if not open_states:
        return None
    return max(open_states, key=lambda s: s.fare)


def find_open_class_by_code(
    states: list[FareClassState], code: str
) -> FareClassState | None:
    for s in states:
        if s.code == code and s.is_open:
            return s
    return None
