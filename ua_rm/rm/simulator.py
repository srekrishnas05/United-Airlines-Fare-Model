"""Main simulation loop — assembles everything end-to-end."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta

import numpy as np

from ua_rm.config.aircraft import Aircraft, get_aircraft
from ua_rm.config.fare_classes import fares_for_cabin
from ua_rm.config.routes import Route, get_route
from ua_rm.params import (
    AWARD_RELEASE_PACING_THRESHOLD,
    NO_SHOW_RATE,
)
from ua_rm.pricing.engine import compute_wtp
from ua_rm.rm.bid_price import compute_bid_price
from ua_rm.rm.booking_curve import (
    BookingCurve,
    build_booking_curves,
    pacing_ratio,
)
from ua_rm.rm.demand import (
    DemandSegment,
    build_demand_segments,
    maybe_award_arrivals,
    maybe_group_event,
    simulate_arrivals,
)
from ua_rm.rm.emsr import compute_protection_levels, total_protection
from ua_rm.rm.fare_controller import (
    FareClassState,
    find_open_class_by_code,
    lowest_open_class,
    update_fare_classes,
)
from ua_rm.rm.inventory import Booking, FlightInventory, build_inventory


CABINS: tuple[str, ...] = ("J", "W", "Y")


@dataclass
class SimConfig:
    route_code: str
    aircraft_code: str
    departure_date: date
    booking_window_days: int = 365
    time_step_days: int = 1
    random_seed: int = 42
    add_noise: bool = True


@dataclass
class TimeStepRecord:
    days_out: int
    query_date: date
    wtp: dict[str, float]
    bid_prices: dict[str, float]
    pacing_ratios: dict[str, float]
    fare_states: dict[str, list[dict]]   # cabin -> [state-as-dict]
    inventory_snapshot: dict
    bookings_this_step: int
    group_bookings_this_step: int
    award_bookings_this_step: int

    def to_dict(self) -> dict:
        return {
            "days_out": self.days_out,
            "query_date": self.query_date.isoformat(),
            "wtp": self.wtp,
            "bid_prices": self.bid_prices,
            "pacing_ratios": self.pacing_ratios,
            "fare_states": self.fare_states,
            "inventory_snapshot": self.inventory_snapshot,
            "bookings_this_step": self.bookings_this_step,
            "group_bookings_this_step": self.group_bookings_this_step,
            "award_bookings_this_step": self.award_bookings_this_step,
        }


@dataclass
class SimResult:
    config: SimConfig
    history: list[TimeStepRecord]
    final_inventory: FlightInventory
    no_shows_by_cabin: dict[str, int] = field(default_factory=dict)
    denied_boarding_by_cabin: dict[str, int] = field(default_factory=dict)

    @property
    def total_revenue(self) -> float:
        return sum(b.fare_paid for b in self.final_inventory.bookings if not b.no_show)

    @property
    def revenue_by_cabin(self) -> dict[str, float]:
        out: dict[str, float] = {c: 0.0 for c in CABINS}
        for b in self.final_inventory.bookings:
            if b.no_show:
                continue
            out[b.cabin] += b.fare_paid
        return out

    @property
    def load_factor(self) -> dict[str, float]:
        out: dict[str, float] = {}
        boarded_total = 0
        capacity_total = 0
        for c in CABINS:
            inv = self.final_inventory[c]
            boarded = inv.seats_sold
            out[c] = boarded / inv.total_seats if inv.total_seats > 0 else 0.0
            boarded_total += boarded
            capacity_total += inv.total_seats
        out["overall"] = boarded_total / capacity_total if capacity_total > 0 else 0.0
        return out

    @property
    def avg_fare_by_cabin(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for c in CABINS:
            paid = [b.fare_paid for b in self.final_inventory.bookings
                    if b.cabin == c and not b.no_show]
            out[c] = float(np.mean(paid)) if paid else 0.0
        return out


# --------------------------------------------------------------------------
# Booking helpers
# --------------------------------------------------------------------------

def _book_passenger(
    arrival_segment: str,
    arrival_cabin: str,
    arrival_wtp_factor: float,
    cabin_wtp: dict[str, float],
    fare_states: dict[str, list[FareClassState]],
    inventory: FlightInventory,
    days_out: int,
) -> Booking | None:
    """Try to seat an arriving passenger; return the booking or None if walked."""
    # Try preferred cabin first; if no affordable open class, try down-shift to
    # cheaper cabins (W -> Y for elastic, never up-sell).
    cabin_priority = {
        "J": ["J", "W", "Y"],
        "W": ["W", "Y"],
        "Y": ["Y"],
    }[arrival_cabin]

    for cabin in cabin_priority:
        if inventory[cabin].bookable_seats <= 0:
            continue
        states = fare_states[cabin]
        max_fare = arrival_wtp_factor * cabin_wtp[cabin]
        chosen = lowest_open_class(states, max_fare_factor=max_fare)
        if chosen is None:
            continue
        return Booking(
            cabin=cabin,
            fare_class=chosen.code,
            fare_paid=chosen.fare,
            days_out=days_out,
        )
    return None


def _apply_group_event(
    event,
    fare_states: dict[str, list[FareClassState]],
    inventory: FlightInventory,
    rng: np.random.Generator,
) -> int:
    """Returns number of group seats actually booked."""
    cabin = event.cabin
    cabin_inv = inventory[cabin]
    seats_wanted = event.size
    available = cabin_inv.bookable_seats
    if available <= 0:
        return 0

    chosen = find_open_class_by_code(fare_states[cabin], event.fare_class)
    if chosen is None:
        # Fallback to highest open class in cabin
        from ua_rm.rm.fare_controller import highest_open_class
        chosen = highest_open_class(fare_states[cabin])
        if chosen is None:
            return 0

    if available < seats_wanted:
        if rng.random() < 0.4:
            seats_to_book = available
        else:
            return 0  # group walks
    else:
        seats_to_book = seats_wanted

    fare = chosen.fare * event.discount_factor
    for _ in range(seats_to_book):
        inventory.record_booking(Booking(
            cabin=cabin,
            fare_class=chosen.code,
            fare_paid=fare,
            days_out=event.days_out,
            is_group=True,
        ))
    return seats_to_book


def _apply_award_arrivals(
    arrivals,
    inventory: FlightInventory,
    days_out: int,
) -> int:
    booked = 0
    for a in arrivals:
        cabin_inv = inventory[a.cabin]
        if cabin_inv.bookable_seats <= 0:
            continue
        inventory.record_booking(Booking(
            cabin=a.cabin,
            fare_class=a.fare_class,
            fare_paid=a.redemption_value,
            days_out=days_out,
            is_award=True,
        ))
        booked += 1
    return booked


# --------------------------------------------------------------------------
# No-show / overbooking resolution
# --------------------------------------------------------------------------

def _resolve_departure(
    inventory: FlightInventory, rng: np.random.Generator
) -> tuple[dict[str, int], dict[str, int]]:
    """At days_out=0: roll no-shows, then resolve over-capacity as denied boarding.

    Mutates Bookings in-place (sets no_show / denied_boarding flags) and
    decrements seats_sold to reflect actual boardings.
    """
    no_shows_by_cabin: dict[str, int] = {c: 0 for c in CABINS}
    denied_by_cabin: dict[str, int] = {c: 0 for c in CABINS}

    bookings_by_cabin: dict[str, list[Booking]] = {c: [] for c in CABINS}
    for b in inventory.bookings:
        bookings_by_cabin[b.cabin].append(b)

    for cabin in CABINS:
        rate = NO_SHOW_RATE[cabin]
        cabin_bookings = bookings_by_cabin[cabin]
        for b in cabin_bookings:
            if rng.random() < rate:
                b.no_show = True
                no_shows_by_cabin[cabin] += 1

        showed_up = [b for b in cabin_bookings if not b.no_show]
        capacity = inventory[cabin].total_seats
        overflow = len(showed_up) - capacity
        if overflow > 0:
            # Deny boarding to the lowest-fare passengers first
            showed_up.sort(key=lambda b: b.fare_paid)
            for b in showed_up[:overflow]:
                b.denied_boarding = True
                denied_by_cabin[cabin] += 1

        boarded = sum(
            1 for b in cabin_bookings
            if not b.no_show and not b.denied_boarding
        )
        inventory[cabin].seats_sold = boarded

    return no_shows_by_cabin, denied_by_cabin


# --------------------------------------------------------------------------
# Main loop
# --------------------------------------------------------------------------

def run_simulation(config: SimConfig) -> SimResult:
    rng = np.random.default_rng(config.random_seed)
    route = get_route(config.route_code)
    aircraft = get_aircraft(config.aircraft_code)

    inventory = build_inventory(aircraft)
    curves = build_booking_curves(route, config.booking_window_days)
    segments = build_demand_segments(route)

    history: list[TimeStepRecord] = []

    days_sequence = list(range(
        config.booking_window_days, 0, -config.time_step_days
    ))

    for days_out in days_sequence:
        query_date = config.departure_date - timedelta(days=days_out)

        # A. WTP per cabin
        wtp = {
            cabin: compute_wtp(
                route, aircraft, cabin,
                config.departure_date, query_date,
                add_noise=config.add_noise, rng=rng,
            )
            for cabin in CABINS
        }

        # B. Bid prices per cabin
        bid_prices = {
            cabin: compute_bid_price(
                inventory[cabin], curves[cabin], days_out, wtp[cabin]
            )
            for cabin in CABINS
        }

        # C. EMSR protection levels
        for cabin in CABINS:
            protections = compute_protection_levels(
                cabin, inventory[cabin], curves[cabin], days_out, wtp[cabin]
            )
            inventory[cabin].protected_seats = total_protection(protections)

        # D. Fare class open/close states
        fare_states: dict[str, list[FareClassState]] = {
            cabin: update_fare_classes(
                cabin, wtp[cabin], bid_prices[cabin], inventory[cabin]
            )
            for cabin in CABINS
        }

        # E. Individual demand arrivals
        arrivals = simulate_arrivals(
            segments, days_out, config.time_step_days, rng
        )
        bookings_count = 0
        for a in arrivals:
            booking = _book_passenger(
                a.segment, a.cabin, a.wtp_factor, wtp, fare_states,
                inventory, days_out,
            )
            if booking is not None:
                inventory.record_booking(booking)
                bookings_count += 1

        # F. Group event
        group_count = 0
        event = maybe_group_event(route, days_out, rng)
        if event is not None:
            group_count = _apply_group_event(event, fare_states, inventory, rng)

        # G. Award arrivals (gated by overall pacing)
        overall_sold = sum(inventory[c].seats_sold for c in CABINS)
        overall_total = sum(inventory[c].total_seats for c in CABINS)
        # Use Y curve as proxy for overall pacing
        overall_ratio = pacing_ratio(
            overall_sold, overall_total, curves["Y"], days_out
        )
        award_arrivals = maybe_award_arrivals(
            days_out, config.time_step_days, overall_ratio,
            AWARD_RELEASE_PACING_THRESHOLD, rng,
        )
        award_count = _apply_award_arrivals(
            award_arrivals, inventory, days_out
        )

        # H. Pacing record
        ratios = {
            cabin: pacing_ratio(
                inventory[cabin].seats_sold,
                inventory[cabin].total_seats,
                curves[cabin],
                days_out,
            )
            for cabin in CABINS
        }

        # I. Log
        fare_states_dict = {
            cabin: [
                {
                    "code": s.code,
                    "is_open": s.is_open,
                    "threshold_price": s.threshold_price,
                    "fare": s.fare,
                }
                for s in fare_states[cabin]
            ]
            for cabin in CABINS
        }
        history.append(TimeStepRecord(
            days_out=days_out,
            query_date=query_date,
            wtp=wtp,
            bid_prices=bid_prices,
            pacing_ratios=ratios,
            fare_states=fare_states_dict,
            inventory_snapshot=inventory.snapshot(),
            bookings_this_step=bookings_count,
            group_bookings_this_step=group_count,
            award_bookings_this_step=award_count,
        ))

    # Departure resolution
    no_shows, denied = _resolve_departure(inventory, rng)

    return SimResult(
        config=config,
        history=history,
        final_inventory=inventory,
        no_shows_by_cabin=no_shows,
        denied_boarding_by_cabin=denied,
    )
