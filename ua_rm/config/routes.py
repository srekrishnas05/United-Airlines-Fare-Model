"""Route registry.

Each route drives pricing and demand behavior. No route should be
hard-coded anywhere else — all route-specific logic reads from this
registry.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Route:
    origin: str
    destination: str
    distance_km: int
    region: str               # "south_asia"|"east_asia"|"southeast_asia"|"europe"|"africa"|"middle_east"|"latam"|"oceania"
    demand_profile: str       # "vfr_heavy"|"business_heavy"|"mixed"
    competition_level: str    # "low"|"medium"|"high"
    aircraft_options: tuple[str, ...]
    daily_frequency: int
    holiday_country: str      # ISO country code for destination
    j_yield_tier: str         # "premium"|"standard"|"budget"
    j_seasonality_sensitivity: float  # 0.0 = flat, 1.0 = full seasonal swing

    @property
    def code(self) -> str:
        return f"{self.origin}-{self.destination}"


def _r(
    origin: str, destination: str, distance_km: int, region: str,
    demand_profile: str, competition_level: str,
    aircraft_options: tuple[str, ...], daily_frequency: int,
    holiday_country: str, j_yield_tier: str, j_seasonality_sensitivity: float,
) -> Route:
    return Route(
        origin=origin, destination=destination, distance_km=distance_km,
        region=region, demand_profile=demand_profile,
        competition_level=competition_level,
        aircraft_options=aircraft_options, daily_frequency=daily_frequency,
        holiday_country=holiday_country, j_yield_tier=j_yield_tier,
        j_seasonality_sensitivity=j_seasonality_sensitivity,
    )


_ROUTES: list[Route] = [
    # ---- EWR (Newark) ----
    _r("EWR", "CDG", 5851, "europe",         "business_heavy", "high",   ("763", "772"), 2, "FR", "standard", 1.0),
    _r("EWR", "NCE", 6473, "europe",         "mixed",          "medium", ("763",),       1, "FR", "standard", 0.85),
    _r("EWR", "FRA", 6207, "europe",         "business_heavy", "high",   ("763", "789"), 2, "DE", "standard", 1.0),
    _r("EWR", "MUC", 6485, "europe",         "business_heavy", "high",   ("763", "789"), 1, "DE", "standard", 0.95),
    _r("EWR", "AMS", 5854, "europe",         "business_heavy", "high",   ("767",),       1, "NL", "standard", 0.95),
    _r("EWR", "BRU", 5874, "europe",         "business_heavy", "medium", ("781",),       1, "BE", "standard", 0.9),
    _r("EWR", "ZRH", 6320, "europe",         "business_heavy", "medium", ("763",),       1, "CH", "premium",  0.7),
    _r("EWR", "GVA", 6232, "europe",         "business_heavy", "medium", ("763",),       1, "CH", "premium",  0.7),
    _r("EWR", "FCO", 6906, "europe",         "business_heavy", "high",   ("763",),       1, "IT", "standard", 0.85),
    _r("EWR", "MXP", 6500, "europe",         "mixed",          "medium", ("772",),       1, "IT", "standard", 0.8),
    _r("EWR", "BCN", 6171, "europe",         "business_heavy", "medium", ("763",),       1, "ES", "standard", 0.8),
    _r("EWR", "MAD", 5764, "europe",         "business_heavy", "medium", ("763",),       1, "ES", "standard", 0.85),
    _r("EWR", "LIS", 5419, "europe",         "business_heavy", "medium", ("781",),       1, "PT", "standard", 0.8),
    _r("EWR", "ATH", 7900, "europe",         "business_heavy", "low",    ("781",),       1, "GR", "premium",  0.7),
    _r("EWR", "DUB", 5141, "europe",         "business_heavy", "medium", ("772",),       1, "IE", "standard", 0.85),
    _r("EWR", "DEL", 12050, "south_asia",    "business_heavy", "low",    ("77W",),       1, "IN", "premium",  0.0),
    _r("EWR", "CPT", 12555, "africa",        "mixed",          "low",    ("789",),       1, "ZA", "premium",  0.4),
    _r("EWR", "JNB", 12830, "africa",        "mixed",          "low",    ("789",),       1, "ZA", "premium",  0.4),
    _r("EWR", "DXB", 11020, "middle_east",   "business_heavy", "low",    ("77W",),       1, "AE", "premium",  0.0),
    _r("EWR", "TLV", 9100,  "middle_east",   "business_heavy", "medium", ("789",),       1, "IL", "premium",  0.3),
    _r("EWR", "HND", 10880, "east_asia",     "mixed",          "medium", ("789",),       1, "JP", "premium",  0.5),
    _r("EWR", "NRT", 10860, "east_asia",     "mixed",          "medium", ("789",),       1, "JP", "premium",  0.5),
    _r("EWR", "ICN", 11062, "east_asia",     "business_heavy", "low",    ("789",),       1, "KR", "premium",  0.5),
    _r("EWR", "GRU", 7700,  "latam",         "mixed",          "medium", ("787",),       1, "BR", "standard", 0.7),
    _r("EWR", "EZE", 8520,  "latam",         "business_heavy", "low",    ("772",),       1, "AR", "premium",  0.6),

    # ---- IAD (Dulles) ----
    _r("IAD", "CDG", 6168, "europe",         "business_heavy", "high",   ("763",),       1, "FR", "standard", 1.0),
    _r("IAD", "FRA", 6504, "europe",         "business_heavy", "high",   ("763",),       1, "DE", "standard", 1.0),
    _r("IAD", "MUC", 6826, "europe",         "business_heavy", "medium", ("763",),       1, "DE", "standard", 0.95),
    _r("IAD", "AMS", 6167, "europe",         "business_heavy", "high",   ("767",),       1, "NL", "standard", 0.95),
    _r("IAD", "BRU", 6201, "europe",         "business_heavy", "medium", ("781",),       1, "BE", "standard", 0.9),
    _r("IAD", "ZRH", 6633, "europe",         "business_heavy", "medium", ("763",),       1, "CH", "premium",  0.7),
    _r("IAD", "GVA", 6519, "europe",         "business_heavy", "medium", ("763",),       1, "CH", "premium",  0.7),
    _r("IAD", "FCO", 7244, "europe",         "business_heavy", "medium", ("763",),       1, "IT", "standard", 0.85),
    _r("IAD", "BCN", 6463, "europe",         "business_heavy", "medium", ("763",),       1, "ES", "standard", 0.8),
    _r("IAD", "MAD", 6062, "europe",         "business_heavy", "medium", ("763",),       1, "ES", "standard", 0.85),
    _r("IAD", "LIS", 5697, "europe",         "business_heavy", "medium", ("781",),       1, "PT", "standard", 0.8),
    _r("IAD", "DUB", 5503, "europe",         "business_heavy", "medium", ("772",),       1, "IE", "standard", 0.85),
    _r("IAD", "CPT", 12490, "africa",        "mixed",          "low",    ("789",),       1, "ZA", "premium",  0.4),
    _r("IAD", "JNB", 12762, "africa",        "mixed",          "low",    ("789",),       1, "ZA", "premium",  0.4),
    _r("IAD", "ACC", 8740,  "africa",        "vfr_heavy",      "low",    ("763",),       1, "GH", "budget",   0.85),
    _r("IAD", "DSS", 6850,  "africa",        "vfr_heavy",      "low",    ("763",),       1, "SN", "budget",   0.85),
    _r("IAD", "LOS", 9020,  "africa",        "vfr_heavy",      "low",    ("763",),       1, "NG", "budget",   0.85),
    _r("IAD", "HND", 11150, "east_asia",     "mixed",          "medium", ("789",),       1, "JP", "premium",  0.5),
    _r("IAD", "NRT", 11118, "east_asia",     "mixed",          "medium", ("789",),       1, "JP", "premium",  0.5),
    _r("IAD", "GRU", 7722,  "latam",         "mixed",          "medium", ("787",),       1, "BR", "standard", 0.7),
    _r("IAD", "EZE", 8500,  "latam",         "business_heavy", "low",    ("772",),       1, "AR", "premium",  0.6),

    # ---- ORD (Chicago) ----
    _r("ORD", "CDG", 6661, "europe",         "business_heavy", "high",   ("772",),       1, "FR", "standard", 1.0),
    _r("ORD", "FRA", 7095, "europe",         "business_heavy", "high",   ("77W",),       1, "DE", "standard", 1.0),
    _r("ORD", "MUC", 7376, "europe",         "business_heavy", "medium", ("789",),       1, "DE", "standard", 0.95),
    _r("ORD", "AMS", 6760, "europe",         "business_heavy", "high",   ("788",),       1, "NL", "standard", 0.95),
    _r("ORD", "BRU", 6792, "europe",         "business_heavy", "medium", ("781",),       1, "BE", "standard", 0.9),
    _r("ORD", "ZRH", 7180, "europe",         "business_heavy", "medium", ("763",),       1, "CH", "premium",  0.7),
    _r("ORD", "GVA", 7060, "europe",         "business_heavy", "medium", ("763",),       1, "CH", "premium",  0.7),
    _r("ORD", "FCO", 7757, "europe",         "business_heavy", "medium", ("778",),       1, "IT", "standard", 0.85),
    _r("ORD", "DUB", 6065, "europe",         "business_heavy", "medium", ("778",),       1, "IE", "standard", 0.85),
    _r("ORD", "HND", 10145, "east_asia",     "mixed",          "medium", ("789",),       1, "JP", "premium",  0.5),
    _r("ORD", "NRT", 10135, "east_asia",     "mixed",          "medium", ("789",),       1, "JP", "premium",  0.5),

    # ---- IAH (Houston) ----
    _r("IAH", "FRA", 8307, "europe",         "business_heavy", "medium", ("77W",),       1, "DE", "standard", 0.9),
    _r("IAH", "MUC", 8579, "europe",         "business_heavy", "low",    ("789",),       1, "DE", "premium",  0.7),
    _r("IAH", "AMS", 8000, "europe",         "business_heavy", "medium", ("788",),       1, "NL", "standard", 0.85),
    _r("IAH", "BRU", 8027, "europe",         "business_heavy", "low",    ("781",),       1, "BE", "premium",  0.7),
    _r("IAH", "ZRH", 8390, "europe",         "business_heavy", "low",    ("789",),       1, "CH", "premium",  0.6),
    _r("IAH", "GVA", 8274, "europe",         "business_heavy", "low",    ("789",),       1, "CH", "premium",  0.6),
    _r("IAH", "FCO", 9000, "europe",         "business_heavy", "medium", ("789",),       1, "IT", "standard", 0.85),
    _r("IAH", "DUB", 7300, "europe",         "business_heavy", "medium", ("789",),       1, "IE", "standard", 0.85),
    _r("IAH", "GRU", 7942, "latam",          "mixed",          "medium", ("787",),       1, "BR", "standard", 0.7),
    _r("IAH", "EZE", 8440, "latam",          "business_heavy", "low",    ("772",),       1, "AR", "premium",  0.6),
    _r("IAH", "LIM", 4750, "latam",          "business_heavy", "medium", ("763",),       1, "PE", "standard", 0.7),
    _r("IAH", "SYD", 13830, "oceania",       "business_heavy", "low",    ("789",),       1, "AU", "premium",  0.5),

    # ---- SFO (San Francisco) ----
    _r("SFO", "SIN", 13586, "southeast_asia","business_heavy", "low",    ("789L",),      1, "SG", "premium",  0.0),
    _r("SFO", "HKG", 11148, "east_asia",     "mixed",          "medium", ("77W",),       1, "HK", "premium",  0.5),
    _r("SFO", "ICN", 9043,  "east_asia",     "mixed",          "medium", ("77W",),       1, "KR", "standard", 0.5),
    _r("SFO", "HND", 8285,  "east_asia",     "mixed",          "medium", ("789",),       1, "JP", "premium",  0.5),
    _r("SFO", "NRT", 8283,  "east_asia",     "mixed",          "medium", ("789",),       1, "JP", "premium",  0.5),
    _r("SFO", "TPE", 10921, "east_asia",     "mixed",          "low",    ("77W",),       1, "TW", "premium",  0.4),
    _r("SFO", "FRA", 9135,  "europe",        "business_heavy", "medium", ("77W",),       1, "DE", "standard", 0.95),
    _r("SFO", "MUC", 9433,  "europe",        "business_heavy", "low",    ("789",),       1, "DE", "premium",  0.7),
    _r("SFO", "MNL", 11270, "east_asia",     "mixed",          "low",    ("77W",),       1, "PH", "budget",   0.7),
    _r("SFO", "AKL", 10499, "oceania",       "business_heavy", "low",    ("77W",),       1, "NZ", "premium",  0.4),
    _r("SFO", "MEL", 12660, "oceania",       "business_heavy", "low",    ("789",),       1, "AU", "premium",  0.4),
    _r("SFO", "SYD", 11930, "oceania",       "business_heavy", "medium", ("789",),       1, "AU", "premium",  0.5),
    _r("SFO", "BNE", 11540, "oceania",       "business_heavy", "low",    ("789",),       1, "AU", "premium",  0.4),
]


ROUTES: dict[str, Route] = {r.code: r for r in _ROUTES}


def get_route(code: str) -> Route:
    if code not in ROUTES:
        raise KeyError(
            f"Unknown route '{code}'. Known: {sorted(ROUTES.keys())[:8]}..."
        )
    return ROUTES[code]
