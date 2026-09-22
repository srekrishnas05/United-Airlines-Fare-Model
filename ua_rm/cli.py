"""CLI entry point: `python -m ua_rm <command>`."""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

from ua_rm.analysis.plots import write_all_plots
from ua_rm.analysis.report import print_summary, write_outputs
from ua_rm.config.aircraft import AIRCRAFT
from ua_rm.config.routes import ROUTES
from ua_rm.rm.simulator import SimConfig, run_simulation


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def cmd_simulate(args: argparse.Namespace) -> int:
    if args.route not in ROUTES:
        print(f"Unknown route: {args.route}", file=sys.stderr)
        return 1
    if args.aircraft not in AIRCRAFT:
        print(f"Unknown aircraft: {args.aircraft}", file=sys.stderr)
        return 1

    config = SimConfig(
        route_code=args.route,
        aircraft_code=args.aircraft,
        departure_date=args.departure,
        booking_window_days=args.window,
        time_step_days=args.step,
        random_seed=args.seed,
        add_noise=not args.no_noise,
    )
    print(f"Running simulation for {config.route_code} on {config.departure_date}...")
    result = run_simulation(config)
    print_summary(result)

    out_root = Path(args.output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = out_root / f"{config.route_code}_{config.departure_date}_{timestamp}"
    write_outputs(result, run_dir)
    print(f"Results written to: {run_dir}")

    if args.plot:
        plot_paths = write_all_plots(result, run_dir)
        print("Plots:")
        for p in plot_paths:
            print(f"  - {p}")
    return 0


def cmd_routes(_args: argparse.Namespace) -> int:
    print(f"{'Route':<10}{'Distance':>10}  {'Region':<16}{'Profile':<18}"
          f"{'Comp':<8}{'Aircraft':<14}")
    for code in sorted(ROUTES.keys()):
        r = ROUTES[code]
        print(f"{code:<10}{r.distance_km:>10}  {r.region:<16}{r.demand_profile:<18}"
              f"{r.competition_level:<8}{','.join(r.aircraft_options):<14}")
    print(f"\nTotal: {len(ROUTES)} routes")
    return 0


def cmd_aircraft(_args: argparse.Namespace) -> int:
    print(f"{'Code':<6}{'Name':<14}{'J':>5}{'W':>5}{'Y':>5}{'Total':>7}")
    for code, ac in AIRCRAFT.items():
        print(f"{ac.code:<6}{ac.name:<14}{ac.seats_j:>5}{ac.seats_w:>5}"
              f"{ac.seats_y:>5}{ac.total_seats:>7}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m ua_rm",
        description="UA Pricing Engine V2 — single-flight RM simulation.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_sim = sub.add_parser("simulate", help="Run a single simulation")
    p_sim.add_argument("--route", required=True, help="Route code, e.g. EWR-DEL")
    p_sim.add_argument("--aircraft", required=True, help="Aircraft code, e.g. 77W")
    p_sim.add_argument("--departure", required=True, type=_parse_date,
                       help="Departure date YYYY-MM-DD")
    p_sim.add_argument("--window", type=int, default=365,
                       help="Booking window in days (default 365)")
    p_sim.add_argument("--step", type=int, default=1,
                       help="Time step in days (default 1)")
    p_sim.add_argument("--seed", type=int, default=42,
                       help="Random seed (default 42)")
    p_sim.add_argument("--no-noise", action="store_true",
                       help="Disable WTP and demand noise (deterministic)")
    p_sim.add_argument("--output-dir", default="data/outputs",
                       help="Where to write run outputs")
    p_sim.add_argument("--plot", action="store_true",
                       help="Generate the four standard plots")
    p_sim.set_defaults(func=cmd_simulate)

    p_routes = sub.add_parser("routes", help="List available routes")
    p_routes.set_defaults(func=cmd_routes)

    p_ac = sub.add_parser("aircraft", help="List aircraft configs")
    p_ac.set_defaults(func=cmd_aircraft)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
