"""Console report and JSON/CSV serialization for SimResult."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from ua_rm.rm.simulator import CABINS, SimResult


def _config_to_dict(cfg) -> dict:
    return {
        "route_code": cfg.route_code,
        "aircraft_code": cfg.aircraft_code,
        "departure_date": cfg.departure_date.isoformat(),
        "booking_window_days": cfg.booking_window_days,
        "time_step_days": cfg.time_step_days,
        "random_seed": cfg.random_seed,
        "add_noise": cfg.add_noise,
    }


def write_outputs(result: SimResult, base_dir: Path) -> Path:
    """Writes config.json, history.csv, fare_availability.csv, summary.json.

    Returns the run directory path.
    """
    base_dir.mkdir(parents=True, exist_ok=True)

    # config.json
    with open(base_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(_config_to_dict(result.config), f, indent=2)

    # history.csv — flat per-step record
    history_path = base_dir / "history.csv"
    with open(history_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["days_out", "query_date"]
        for c in CABINS:
            header += [f"wtp_{c}", f"bid_{c}", f"pacing_{c}",
                       f"sold_{c}", f"available_{c}", f"protected_{c}",
                       f"load_factor_{c}"]
        header += ["bookings_this_step", "group_bookings_this_step",
                   "award_bookings_this_step"]
        writer.writerow(header)
        for rec in result.history:
            row = [rec.days_out, rec.query_date.isoformat()]
            snap = rec.inventory_snapshot
            for c in CABINS:
                row += [
                    f"{rec.wtp[c]:.2f}",
                    f"{rec.bid_prices[c]:.2f}",
                    f"{rec.pacing_ratios[c]:.4f}",
                    snap[c]["seats_sold"],
                    snap[c]["seats_available"],
                    snap[c]["protected_seats"],
                    f"{snap[c]['load_factor']:.4f}",
                ]
            row += [
                rec.bookings_this_step,
                rec.group_bookings_this_step,
                rec.award_bookings_this_step,
            ]
            writer.writerow(row)

    # fare_availability.csv — wide format, one row per timestep, one column per fare class
    fa_path = base_dir / "fare_availability.csv"
    if result.history:
        all_codes: list[str] = []
        for c in CABINS:
            for s in result.history[0].fare_states[c]:
                all_codes.append(s["code"])
        with open(fa_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["days_out"] + all_codes)
            for rec in result.history:
                row = [rec.days_out]
                code_to_open: dict[str, int] = {}
                for c in CABINS:
                    for s in rec.fare_states[c]:
                        code_to_open[s["code"]] = 1 if s["is_open"] else 0
                row += [code_to_open.get(code, 0) for code in all_codes]
                writer.writerow(row)

    # summary.json — derived stats
    summary = {
        "total_revenue": result.total_revenue,
        "revenue_by_cabin": result.revenue_by_cabin,
        "load_factor": result.load_factor,
        "avg_fare_by_cabin": result.avg_fare_by_cabin,
        "no_shows_by_cabin": result.no_shows_by_cabin,
        "denied_boarding_by_cabin": result.denied_boarding_by_cabin,
        "bookings_total": len(result.final_inventory.bookings),
        "bookings_by_cabin": {
            c: sum(1 for b in result.final_inventory.bookings if b.cabin == c)
            for c in CABINS
        },
        "group_bookings_total": sum(
            1 for b in result.final_inventory.bookings if b.is_group
        ),
        "award_bookings_total": sum(
            1 for b in result.final_inventory.bookings if b.is_award
        ),
    }
    with open(base_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return base_dir


def print_summary(result: SimResult) -> None:
    cfg = result.config
    print()
    print("=" * 70)
    print(f" Simulation: {cfg.route_code}  aircraft={cfg.aircraft_code}  "
          f"departure={cfg.departure_date}")
    print(f" Window={cfg.booking_window_days}d  step={cfg.time_step_days}d  "
          f"seed={cfg.random_seed}  noise={cfg.add_noise}")
    print("=" * 70)

    lf = result.load_factor
    rev = result.revenue_by_cabin
    avg = result.avg_fare_by_cabin
    print(f"\n{'Cabin':<8}{'Seats':>8}{'Sold':>8}{'LF':>8}"
          f"{'AvgFare':>12}{'Revenue':>14}")
    for c in CABINS:
        inv = result.final_inventory[c]
        print(f"{c:<8}{inv.total_seats:>8}{inv.seats_sold:>8}"
              f"{lf[c]*100:>7.1f}%"
              f"{avg[c]:>12,.0f}{rev[c]:>14,.0f}")
    print("-" * 58)
    print(f"{'TOTAL':<8}{sum(result.final_inventory[c].total_seats for c in CABINS):>8}"
          f"{sum(result.final_inventory[c].seats_sold for c in CABINS):>8}"
          f"{lf['overall']*100:>7.1f}%"
          f"{'':>12}{result.total_revenue:>14,.0f}")

    print(f"\nNo-shows:        {result.no_shows_by_cabin}")
    print(f"Denied boarding: {result.denied_boarding_by_cabin}")
    print(f"Group bookings:  "
          f"{sum(1 for b in result.final_inventory.bookings if b.is_group)}")
    print(f"Award bookings:  "
          f"{sum(1 for b in result.final_inventory.bookings if b.is_award)}")
    print()
