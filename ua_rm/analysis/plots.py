"""Standard sim plots — saved alongside the run outputs."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless for batch runs

import matplotlib.pyplot as plt
import numpy as np

from ua_rm.config.fare_classes import (
    BUSINESS_CLASSES,
    ECONOMY_CLASSES,
    PREMIUM_ECONOMY_CLASSES,
)
from ua_rm.rm.booking_curve import BookingCurve, build_booking_curves
from ua_rm.rm.simulator import CABINS, SimResult
from ua_rm.config.routes import get_route


_CABIN_COLORS = {"J": "#1f77b4", "W": "#2ca02c", "Y": "#d62728"}


def _all_fare_codes() -> list[str]:
    # Top to bottom by yield, J first then W then Y
    return BUSINESS_CLASSES + PREMIUM_ECONOMY_CLASSES + ECONOMY_CLASSES


def plot_fare_availability_heatmap(result: SimResult, out_path: Path) -> None:
    codes = _all_fare_codes()
    days_out = [rec.days_out for rec in result.history]
    matrix = np.zeros((len(codes), len(days_out)))
    for col, rec in enumerate(result.history):
        for cabin in CABINS:
            for s in rec.fare_states[cabin]:
                if s["code"] in codes:
                    row = codes.index(s["code"])
                    matrix[row, col] = 1.0 if s["is_open"] else 0.0
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.imshow(
        matrix, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1,
        extent=[max(days_out), min(days_out), len(codes) - 0.5, -0.5],
        interpolation="nearest",
    )
    ax.set_yticks(range(len(codes)))
    ax.set_yticklabels(codes)
    ax.set_xlabel("Days to departure")
    ax.set_ylabel("Fare class (J top → K bottom)")
    ax.set_title(
        f"Fare availability — {result.config.route_code} "
        f"{result.config.aircraft_code}  {result.config.departure_date}"
    )
    ax.invert_xaxis()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plot_bid_price_curves(result: SimResult, out_path: Path) -> None:
    days_out = np.array([rec.days_out for rec in result.history])
    fig, ax = plt.subplots(figsize=(11, 6))
    for cabin in CABINS:
        wtp = [rec.wtp[cabin] for rec in result.history]
        bid = [rec.bid_prices[cabin] for rec in result.history]
        color = _CABIN_COLORS[cabin]
        ax.plot(days_out, wtp, color=color, linestyle="--", alpha=0.6,
                label=f"{cabin} WTP")
        ax.plot(days_out, bid, color=color, linewidth=2,
                label=f"{cabin} Bid Price")
    ax.set_xlabel("Days to departure")
    ax.set_ylabel("Price (USD)")
    ax.set_title(f"Bid price vs WTP — {result.config.route_code}")
    ax.invert_xaxis()
    ax.legend(loc="upper left", fontsize=9, ncol=3)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plot_booking_curve(result: SimResult, out_path: Path) -> None:
    route = get_route(result.config.route_code)
    curves = build_booking_curves(route, result.config.booking_window_days)

    days_out = [rec.days_out for rec in result.history]
    fig, ax = plt.subplots(figsize=(11, 6))
    for cabin in CABINS:
        actual = [rec.inventory_snapshot[cabin]["seats_sold"]
                  / max(rec.inventory_snapshot[cabin]["total_seats"], 1)
                  for rec in result.history]
        expected = [curves[cabin].fraction_at(d) for d in days_out]
        color = _CABIN_COLORS[cabin]
        ax.plot(days_out, actual, color=color, linewidth=2, label=f"{cabin} actual")
        ax.plot(days_out, expected, color=color, linestyle=":", alpha=0.7,
                label=f"{cabin} expected")
    ax.set_xlabel("Days to departure")
    ax.set_ylabel("Fraction of seats sold")
    ax.set_title(f"Booking pacing — {result.config.route_code}")
    ax.invert_xaxis()
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper left", fontsize=9, ncol=3)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plot_revenue_waterfall(result: SimResult, out_path: Path) -> None:
    rev_by_class: dict[str, dict[str, float]] = {c: {} for c in CABINS}
    for b in result.final_inventory.bookings:
        if b.no_show:
            continue
        rev_by_class[b.cabin][b.fare_class] = (
            rev_by_class[b.cabin].get(b.fare_class, 0.0) + b.fare_paid
        )

    fig, ax = plt.subplots(figsize=(12, 6))
    bar_x: list[str] = []
    bar_h: list[float] = []
    bar_c: list[str] = []
    for cabin in CABINS:
        codes_sorted = sorted(rev_by_class[cabin].keys())
        for code in codes_sorted:
            bar_x.append(f"{cabin}/{code}")
            bar_h.append(rev_by_class[cabin][code])
            bar_c.append(_CABIN_COLORS[cabin])
    if not bar_x:
        ax.text(0.5, 0.5, "No revenue recorded", ha="center", va="center")
    else:
        ax.bar(bar_x, bar_h, color=bar_c)
        ax.set_xticks(range(len(bar_x)))
        ax.set_xticklabels(bar_x, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Revenue (USD)")
    ax.set_title(
        f"Revenue by cabin/fare class — {result.config.route_code}  "
        f"Total: ${result.total_revenue:,.0f}"
    )
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def write_all_plots(result: SimResult, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        out_dir / "fare_availability.png",
        out_dir / "bid_price.png",
        out_dir / "booking_curve.png",
        out_dir / "revenue_waterfall.png",
    ]
    plot_fare_availability_heatmap(result, paths[0])
    plot_bid_price_curves(result, paths[1])
    plot_booking_curve(result, paths[2])
    plot_revenue_waterfall(result, paths[3])
    return paths
