"""CLI entry point: build and print a trip itinerary."""

from __future__ import annotations

import sqlite3
import sys

from app_logic import (
    build_itinerary_from_inputs,
    format_itinerary_text,
    initialize_database,
)


def main() -> None:
    print("Travel Planner - itinerary builder\n")

    print("Initializing database (create table and sample data if needed)...")
    try:
        initialize_database()
    except sqlite3.Error as exc:
        print(f"Error: could not initialize database: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Database ready.\n")

    cities_raw = input("Cities (comma-separated): ").strip()
    budget_raw = input("Budget (EGP): ").strip()
    days_raw = input("Number of days: ").strip()

    itinerary, err = build_itinerary_from_inputs(cities_raw, budget_raw, days_raw)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)

    assert itinerary is not None
    print()
    print(format_itinerary_text(itinerary))


if __name__ == "__main__":
    main()
