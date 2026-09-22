"""Seat inventory tracking — absolute counts, per cabin, per booking."""
from __future__ import annotations

from dataclasses import dataclass, field

from ua_rm.config.aircraft import Aircraft
from ua_rm.params import OVERBOOKING_ALLOWANCE


@dataclass
class Booking:
    cabin: str
    fare_class: str
    fare_paid: float
    days_out: int
    is_award: bool = False
    is_group: bool = False
    no_show: bool = False
    denied_boarding: bool = False


@dataclass
class CabinInventory:
    cabin: str
    total_seats: int            # physical capacity
    overbook_cap: int           # physical + allowance — sale ceiling
    seats_sold: int = 0
    protected_seats: int = 0    # set by EMSR

    @property
    def seats_available(self) -> int:
        # Available against the overbooking cap (what we can still *sell*).
        return self.overbook_cap - self.seats_sold

    @property
    def bookable_seats(self) -> int:
        return max(0, self.seats_available - self.protected_seats)

    @property
    def load_factor(self) -> float:
        if self.total_seats <= 0:
            return 0.0
        return self.seats_sold / self.total_seats

    def snapshot(self) -> dict:
        return {
            "cabin": self.cabin,
            "total_seats": self.total_seats,
            "overbook_cap": self.overbook_cap,
            "seats_sold": self.seats_sold,
            "protected_seats": self.protected_seats,
            "seats_available": self.seats_available,
            "bookable_seats": self.bookable_seats,
            "load_factor": self.load_factor,
        }


@dataclass
class FlightInventory:
    cabins: dict[str, CabinInventory]
    bookings: list[Booking] = field(default_factory=list)

    def __getitem__(self, cabin: str) -> CabinInventory:
        return self.cabins[cabin]

    def record_booking(self, booking: Booking) -> None:
        self.cabins[booking.cabin].seats_sold += 1
        self.bookings.append(booking)

    def snapshot(self) -> dict:
        return {c: inv.snapshot() for c, inv in self.cabins.items()}


def build_inventory(aircraft: Aircraft) -> FlightInventory:
    cabins: dict[str, CabinInventory] = {}
    for cabin in ("J", "W", "Y"):
        physical = aircraft.seats_for_cabin(cabin)
        allowance = OVERBOOKING_ALLOWANCE[cabin]
        overbook_cap = int(round(physical * (1.0 + allowance)))
        cabins[cabin] = CabinInventory(
            cabin=cabin,
            total_seats=physical,
            overbook_cap=overbook_cap,
        )
    return FlightInventory(cabins=cabins)
