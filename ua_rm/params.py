"""Calibratable parameters.

These should be tuned empirically once the simulation runs end-to-end.
Keep them in one place rather than scattered through logic.
"""
from __future__ import annotations


# ---------- Pricing — Base Fare ----------
DISTANCE_EXPONENT: float = 0.65

FARE_PER_KM: dict[str, float] = {
    # Calibrated so that EWR-DEL J avg ≈ $8k, Y ≈ $1.3k (industry-typical).
    # Magnitudes in the build note ("0.85 / 0.18 / 0.06") were placeholders.
    "J": 6.0,
    "W": 2.5,
    "Y": 1.5,
}

COMPETITION_FACTOR: dict[str, float] = {
    "low":    1.35,
    "medium": 1.10,
    "high":   0.88,
}

J_YIELD_TIER_FACTOR: dict[str, dict[str, float]] = {
    "J": {"premium": 1.45, "standard": 1.00, "budget": 0.72},
    "W": {"premium": 1.10, "standard": 1.00, "budget": 0.92},
    "Y": {"premium": 1.03, "standard": 1.00, "budget": 0.97},
}


# ---------- Pricing — Seasonality (per region, per month, mostly Y-anchored) ----------
# 1.0 is the route's annual average. Y feels the full swing, J/W are partially
# insulated based on route.j_seasonality_sensitivity.
SEASONALITY_TABLE: dict[str, dict[int, float]] = {
    "europe": {
        1: 0.78, 2: 0.78, 3: 0.88, 4: 1.00, 5: 1.10, 6: 1.25,
        7: 1.35, 8: 1.30, 9: 1.05, 10: 0.95, 11: 0.85, 12: 1.10,
    },
    "south_asia": {
        1: 1.05, 2: 0.95, 3: 0.90, 4: 0.85, 5: 0.80, 6: 0.85,
        7: 0.95, 8: 0.95, 9: 0.95, 10: 1.10, 11: 1.20, 12: 1.30,
    },
    "east_asia": {
        1: 0.90, 2: 0.85, 3: 1.00, 4: 1.10, 5: 1.05, 6: 1.05,
        7: 1.20, 8: 1.20, 9: 1.05, 10: 1.05, 11: 0.95, 12: 1.05,
    },
    "southeast_asia": {
        1: 0.95, 2: 0.95, 3: 1.00, 4: 1.00, 5: 1.00, 6: 1.10,
        7: 1.15, 8: 1.15, 9: 1.00, 10: 0.95, 11: 0.95, 12: 1.20,
    },
    "africa": {
        1: 1.05, 2: 0.95, 3: 0.95, 4: 0.95, 5: 0.90, 6: 1.00,
        7: 1.15, 8: 1.10, 9: 0.95, 10: 0.95, 11: 0.95, 12: 1.20,
    },
    "middle_east": {
        1: 1.00, 2: 0.95, 3: 1.05, 4: 1.05, 5: 0.95, 6: 0.85,
        7: 0.85, 8: 0.90, 9: 1.00, 10: 1.05, 11: 1.05, 12: 1.20,
    },
    "latam": {
        1: 1.25, 2: 1.30, 3: 1.05, 4: 0.90, 5: 0.85, 6: 0.85,
        7: 1.05, 8: 0.95, 9: 0.90, 10: 0.95, 11: 1.00, 12: 1.30,
    },
    "oceania": {
        1: 1.15, 2: 1.05, 3: 1.00, 4: 0.95, 5: 0.85, 6: 0.85,
        7: 0.95, 8: 0.95, 9: 0.90, 10: 0.95, 11: 1.00, 12: 1.35,
    },
}


# ---------- Pricing — Holiday Boost ----------
# Gaussian peak height per holiday strength is rescaled by these constants
HOLIDAY_GAUSSIAN_SIGMA_DAYS: float = 7.0     # width of demand window
HOLIDAY_BASE_PEAK: float = 0.35              # added on top of 1.0 at peak


# ---------- Pricing — TTD ----------
TTD_PARAMS: dict[str, dict[str, float]] = {
    "J": {"L": 1.8, "k": 0.04, "x0": 90.0, "floor": 0.85},
    "W": {"L": 1.5, "k": 0.05, "x0": 60.0, "floor": 0.85},
    "Y": {"L": 1.4, "k": 0.07, "x0": 40.0, "floor": 0.85},
}


# ---------- Pricing — Scarcity (cabin-density driven) ----------
# Reference seat counts per cabin — aircraft with more seats than the
# reference get a small discount; fewer seats → small premium.
SCARCITY_REFERENCE_SEATS: dict[str, int] = {"J": 50, "W": 24, "Y": 200}
SCARCITY_SLOPE: dict[str, float] = {"J": 0.30, "W": 0.20, "Y": 0.15}


# ---------- Pricing — Time-of-Day (kept simple) ----------
TOD_FACTOR_BY_REGION: dict[str, float] = {
    "europe":          1.02,  # popular evening departures
    "south_asia":      1.03,
    "east_asia":       1.02,
    "southeast_asia":  1.02,
    "africa":          1.00,
    "middle_east":     1.01,
    "latam":           1.00,
    "oceania":         1.02,
}


# ---------- Pricing — Noise ----------
WTP_NOISE_SIGMA: float = 0.03


# ---------- Demand ----------
# Daily Poisson arrival rates by route demand profile and segment.
DEMAND_RATES: dict[str, dict[str, float]] = {
    # Peak Poisson lambda (day at the peak of the Gaussian window). Sized so
    # that a typical widebody fills 80-95% on a strong route.
    "vfr_heavy":      {"leisure": 12.0, "business": 1.5},
    "business_heavy": {"leisure": 5.0,  "business": 7.0},
    "mixed":          {"leisure": 8.0,  "business": 4.0},
}

DEMAND_PEAK_DAYS_OUT: dict[str, int] = {"leisure": 55, "business": 8}
DEMAND_WINDOW_SIGMA: dict[str, float] = {"leisure": 30.0, "business": 9.0}

CABIN_PREFERENCE: dict[str, dict[str, float]] = {
    "leisure":  {"Y": 0.86, "W": 0.11, "J": 0.03},
    "business": {"Y": 0.45, "W": 0.18, "J": 0.37},
}

PRICE_ELASTICITY: dict[str, float] = {
    "leisure":  0.85,   # very price-sensitive
    "business": 0.20,   # nearly inelastic
}


# ---------- Booking Curves ----------
# Logistic params per cabin — fraction sold by N days out.
BOOKING_CURVE_PARAMS: dict[str, dict[str, float]] = {
    # Higher k = steeper, x0 = midpoint days_out where 50% expected
    "J": {"k": 0.06, "x0": 25.0, "floor_pct": 0.02},
    "W": {"k": 0.05, "x0": 35.0, "floor_pct": 0.02},
    "Y": {"k": 0.04, "x0": 50.0, "floor_pct": 0.05},
}


# ---------- Bid Price ----------
PACING_RATIO_CLIP: tuple[float, float] = (0.6, 1.5)
SCARCITY_TRIGGER_FRAC: float = 0.20    # below this remaining frac, scarcity bumps bid
SCARCITY_PREMIUM_PEAK: float = 0.40    # max additional bid premium


# ---------- EMSR ----------
# Mean & coefficient-of-variation of remaining demand per cabin used for
# EMSR-b normal approximation. Keyed by (cabin, remaining_window_bucket).
EMSR_DEMAND_COV: float = 0.35


# ---------- No-Shows / Overbooking ----------
NO_SHOW_RATE: dict[str, float] = {"J": 0.05, "W": 0.08, "Y": 0.12}
OVERBOOKING_ALLOWANCE: dict[str, float] = {"J": 0.05, "W": 0.07, "Y": 0.12}


# ---------- Group Bookings ----------
GROUP_DAILY_PROBABILITY: dict[str, float] = {
    "vfr_heavy":      0.06,
    "business_heavy": 0.02,
    "mixed":          0.04,
}
GROUP_SIZE_LAMBDA: float = 22.0
GROUP_SIZE_MIN: int = 10
GROUP_SIZE_MAX: int = 50
GROUP_DISCOUNT: float = 0.85          # 15% off open bucket price
GROUP_PARTIAL_FILL_PROB: float = 0.4
GROUP_FARE_CLASSES: dict[str, list[str]] = {
    "Y": ["H", "Q", "V"],
    "W": ["A", "R"],
}


# ---------- Awards ----------
AVG_AWARDS_PER_MONTH: dict[str, float] = {"J": 1.2, "W": 0.8, "Y": 3.5}
AWARD_RELEASE_PACING_THRESHOLD: float = 0.95
AWARD_REDEMPTION_VALUE_USD: dict[str, float] = {
    # Approximate cash-equivalent value of an award seat (cents/mile × miles)
    "J": 1800.0,
    "W": 700.0,
    "Y": 350.0,
}
AWARD_FARE_CLASS: dict[str, str] = {"J": "Z", "W": "R", "Y": "K"}
