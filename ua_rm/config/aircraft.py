"""Aircraft registry — UA widebody seat configurations.

Aircraft affect two things only: seat counts per cabin, and the seat
density scarcity multiplier. They do not affect product quality or
cost in this model.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Aircraft:
    code: str
    name: str
    seats_j: int
    seats_w: int
    seats_y: int

    @property
    def total_seats(self) -> int:
        return self.seats_j + self.seats_w + self.seats_y

    def seats_for_cabin(self, cabin: str) -> int:
        if cabin == "J":
            return self.seats_j
        if cabin == "W":
            return self.seats_w
        if cabin == "Y":
            return self.seats_y
        raise ValueError(f"Unknown cabin: {cabin}")


AIRCRAFT: dict[str, Aircraft] = {
    "77W": Aircraft("77W", "777-300ER", seats_j=60, seats_w=24, seats_y=266),
    "772": Aircraft("772", "777-200",   seats_j=50, seats_w=24, seats_y=202),
    "789": Aircraft("789", "787-9",     seats_j=48, seats_w=21, seats_y=188),
    "789L": Aircraft("789L", "787-9L",  seats_j=64, seats_w=35, seats_y=123),
    "788": Aircraft("788", "787-8",     seats_j=28, seats_w=21, seats_y=194),
    "781": Aircraft("781", "787-10",    seats_j=44, seats_w=21, seats_y=253),
    "763": Aircraft("763", "767-300ER", seats_j=46, seats_w=22, seats_y=99),
    "764": Aircraft("764", "767-400ER", seats_j=34, seats_w=24, seats_y=173),
}


# Loose codes from the route table that aren't full UA configs — map to a
# representative real config so route entries can use them directly.
AIRCRAFT_ALIASES: dict[str, str] = {
    "767": "763",
    "787": "789",
    "778": "789",
}


def get_aircraft(code: str) -> Aircraft:
    code = AIRCRAFT_ALIASES.get(code, code)
    if code not in AIRCRAFT:
        raise KeyError(
            f"Unknown aircraft '{code}'. Known: {sorted(AIRCRAFT.keys())}"
        )
    return AIRCRAFT[code]
