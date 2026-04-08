"""Shared trip planning logic for CLI and GUI."""

from __future__ import annotations

import sqlite3
import string
from pathlib import Path
from typing import List, Optional, Tuple

from database import DatabaseError
from init_travel_db import init_db
from models import ItineraryDay
from planner import generate_itinerary

DB_PATH = Path(__file__).resolve().parent / "travel.db"
_ALLOWED_CITY_CHARS = frozenset(string.ascii_letters + " ")


def parse_cities(raw: str) -> List[str]:
    return [c.strip() for c in raw.split(",") if c.strip()]


def cities_use_only_letters_and_spaces(cities: List[str]) -> bool:
    return all(all(ch in _ALLOWED_CITY_CHARS for ch in name) for name in cities)


def initialize_database() -> None:
    """Create DB and seed sample rows if needed. Raises ``sqlite3.Error``."""
    init_db(DB_PATH)


def format_itinerary_text(days: List[ItineraryDay]) -> str:
    lines: List[str] = []
    current_city: str = ""
    for d in days:
        city = getattr(d, "city", "")
        if city and city != current_city:
            if current_city:
                lines.append(f"  ✈  Travel to {city}")
                lines.append("")
            lines.append(f"{'─' * 40}")
            lines.append(f"  📍 {city.upper()}")
            lines.append(f"{'─' * 40}")
            lines.append("")
            current_city = city
        lines.append(f"Day {d.day_number}:")
        for p in d.places:
            lines.append(f"  - {p.name} ({p.category}) - {p.price} EGP")
        lines.append(f"  Total: {d.total_cost} EGP")
        lines.append("")
    return "\n".join(lines).rstrip()


def build_itinerary_from_inputs(
    cities_raw: str,
    budget_str: str,
    days_str: str,
) -> Tuple[Optional[List[ItineraryDay]], Optional[str]]:
    """
    Parse and validate inputs, return ``(itinerary, None)`` or ``(None, error)``.
    """
    cities = parse_cities(cities_raw.strip())
    if not cities:
        return None, "Enter at least one city (comma-separated)."
    if not cities_use_only_letters_and_spaces(cities):
        return None, "City names may only contain letters and spaces (A-Z, a-z)."

    try:
        budget = float(budget_str.strip())
    except ValueError:
        return None, "Budget must be a number."

    try:
        num_days = int(days_str.strip())
    except ValueError:
        return None, "Number of days must be a whole number."

    try:
        itinerary = generate_itinerary(cities, budget, num_days)
    except ValueError as exc:
        return None, str(exc)
    except DatabaseError as exc:
        return None, f"Database error: {exc}"

    return itinerary, None
