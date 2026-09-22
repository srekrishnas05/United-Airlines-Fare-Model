"""Holiday calendars for US (origin) and destination countries.

Holidays drive demand spikes via Gaussian boost windows. Each entry is
(month, day, name, demand_boost_strength). Strength is a multiplier on
the peak height of the Gaussian; 1.0 = ordinary, 1.5+ = strong holiday.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Holiday:
    month: int
    day: int
    name: str
    strength: float = 1.0


# Always relevant for outbound from US hubs
US_HOLIDAYS: list[Holiday] = [
    Holiday(1,  1,  "New Year's Day",     1.4),
    Holiday(5,  26, "Memorial Day",       1.2),
    Holiday(7,  4,  "Independence Day",   1.5),
    Holiday(9,  1,  "Labor Day",          1.2),
    Holiday(11, 27, "Thanksgiving",       1.7),
    Holiday(12, 25, "Christmas",          1.8),
]


# Destination-country holidays keyed by ISO country code
DEST_HOLIDAYS: dict[str, list[Holiday]] = {
    "IN": [
        Holiday(10, 24, "Diwali",          1.6),
        Holiday(8,  15, "Independence Day", 1.2),
        Holiday(3,  29, "Holi",            1.2),
    ],
    "FR": [Holiday(7,  14, "Bastille Day",  1.2), Holiday(12, 25, "Christmas", 1.5)],
    "DE": [Holiday(10, 3,  "Unity Day",     1.2), Holiday(12, 25, "Christmas", 1.5)],
    "NL": [Holiday(4,  27, "King's Day",    1.3), Holiday(12, 25, "Christmas", 1.4)],
    "BE": [Holiday(7,  21, "National Day",  1.2), Holiday(12, 25, "Christmas", 1.4)],
    "CH": [Holiday(8,  1,  "Swiss National Day", 1.2)],
    "IT": [Holiday(8,  15, "Ferragosto",    1.5), Holiday(12, 25, "Christmas", 1.4)],
    "ES": [Holiday(10, 12, "Hispanic Day",  1.2), Holiday(12, 25, "Christmas", 1.4)],
    "PT": [Holiday(6,  10, "Portugal Day",  1.2)],
    "GR": [Holiday(3,  25, "Independence Day", 1.2), Holiday(8, 15, "Assumption", 1.4)],
    "IE": [Holiday(3,  17, "St. Patrick's Day", 1.5)],
    "ZA": [Holiday(12, 16, "Day of Reconciliation", 1.3)],
    "AE": [Holiday(12, 2,  "National Day",  1.3)],
    "IL": [Holiday(4,  22, "Passover",      1.4), Holiday(9, 22, "Rosh Hashanah", 1.4)],
    "JP": [Holiday(4,  29, "Golden Week",   1.6), Holiday(8, 13, "Obon",          1.5)],
    "KR": [Holiday(9,  17, "Chuseok",       1.5), Holiday(2,  9,  "Lunar New Year", 1.5)],
    "BR": [Holiday(2,  13, "Carnaval",      1.7), Holiday(9,  7, "Independence Day", 1.2)],
    "AR": [Holiday(5,  25, "Revolution Day", 1.2), Holiday(7, 9,  "Independence Day", 1.2)],
    "GH": [Holiday(3,  6,  "Independence Day", 1.2), Holiday(12, 25, "Christmas",     1.3)],
    "SN": [Holiday(4,  4,  "Independence Day", 1.2)],
    "NG": [Holiday(10, 1,  "Independence Day", 1.2), Holiday(12, 25, "Christmas",    1.3)],
    "HK": [Holiday(2,  10, "Lunar New Year", 1.6), Holiday(10, 1, "National Day",    1.2)],
    "TW": [Holiday(2,  10, "Lunar New Year", 1.5), Holiday(10, 10, "Double Ten",     1.2)],
    "PH": [Holiday(6,  12, "Independence Day", 1.2), Holiday(12, 25, "Christmas",   1.5)],
    "SG": [Holiday(8,   9, "National Day",   1.3), Holiday(2, 10, "Lunar New Year", 1.5)],
    "AU": [Holiday(1,  26, "Australia Day",  1.3), Holiday(12, 25, "Christmas",     1.4)],
    "NZ": [Holiday(2,   6, "Waitangi Day",   1.2)],
    "PE": [Holiday(7,  28, "Independence Day", 1.3)],
}


def holidays_for_route(holiday_country: str) -> list[Holiday]:
    """All holidays relevant for a given route — US plus destination."""
    return US_HOLIDAYS + DEST_HOLIDAYS.get(holiday_country, [])
