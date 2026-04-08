"""Trip planning, recommendations, and budget helpers."""

from __future__ import annotations

import random
from typing import List, Optional, Set, Tuple

from database import get_all_places, get_places_by_city, get_places_filtered
from models import ItineraryDay, Place, Trip

_TOP_N = 5
_DEFAULT_RATING_CAP = 5.0
_MIN_DISTINCT_CATEGORIES_PER_DAY = 3
_TOP_K_RANDOM = 5  # pick randomly among the best-rated candidates for variety


class TravelPlanner:
    """Interactive CLI: list places, pick one, attach to a one-day `Trip`."""

    def __init__(self, places: Optional[List[Place]] = None) -> None:
        self.places = list(places) if places is not None else get_all_places()
        self.trip = Trip(cities=[], budget=10**9, number_of_days=1)

    def show_places(self) -> None:
        print("Available Places:")
        for idx, place in enumerate(self.places, 1):
            print(f"{idx}. {place.name} — {place.city} ({place.category}) · {place.price} · ★ {place.rating}")

    def select_place(self, index: int) -> Optional[Place]:
        if 0 <= index < len(self.places):
            return self.places[index]
        print("Invalid selection.")
        return None

    def run(self) -> None:
        self.show_places()
        choice = input("Select a place to add to your trip (number): ")
        try:
            idx = int(choice) - 1
            place = self.select_place(idx)
            if place:
                self.trip.add_place_to_day(1, place)
                print(f"{place.name} added to your trip!")
        except ValueError:
            print("Please enter a valid number.")


def _price_reference(
    places: List[Place],
    max_price: Optional[int],
    price_budget: Optional[float],
) -> float:
    """
    Budget used to score price: lower price vs this reference earns a higher slice.

    Uses ``price_budget`` when given, else ``max_price``, else the max price in
    ``places`` (minimum 1.0 to avoid division by zero).
    """
    if price_budget is not None and price_budget > 0:
        return float(price_budget)
    if max_price is not None and max_price > 0:
        return float(max_price)
    if places:
        hi = max(p.price for p in places)
        return float(hi) if hi > 0 else 1.0
    return 1.0


def recommendation_score(
    place: Place,
    *,
    price_reference: float,
    rating_cap: float = _DEFAULT_RATING_CAP,
    rating_weight: float = 1.0,
    price_weight: float = 1.0,
) -> float:
    """
    Linear blend of normalized rating (higher better) and price value (cheaper
    vs ``price_reference`` is better). All inputs are clamped to sensible ranges.

    Adjust ``rating_weight`` / ``price_weight`` to favour stars vs savings.
    ``rating_cap`` should match your scale (default 5.0).
    """
    if rating_cap <= 0:
        raise ValueError("rating_cap must be positive")
    if rating_weight < 0 or price_weight < 0:
        raise ValueError("weights must be non-negative")
    if rating_weight == 0 and price_weight == 0:
        raise ValueError("at least one of rating_weight or price_weight must be positive")

    r_norm = max(0.0, min(1.0, place.rating / rating_cap))
    ref = max(price_reference, 1e-9)
    p_norm = max(0.0, min(1.0, 1.0 - place.price / ref))
    return rating_weight * r_norm + price_weight * p_norm


def _recommendation_sort_key(
    place: Place,
    *,
    price_reference: float,
    rating_cap: float,
    rating_weight: float,
    price_weight: float,
) -> Tuple[float, float, str]:
    score = recommendation_score(
        place,
        price_reference=price_reference,
        rating_cap=rating_cap,
        rating_weight=rating_weight,
        price_weight=price_weight,
    )
    return (-score, -place.rating, place.name.lower())


def recommend_places(
    city: str,
    category: str,
    *,
    max_price: Optional[int] = None,
    min_rating: Optional[float] = None,
    price_budget: Optional[float] = None,
    rating_weight: float = 1.0,
    price_weight: float = 1.0,
    rating_cap: float = _DEFAULT_RATING_CAP,
    limit: int = _TOP_N,
) -> List[Place]:
    """
    Recommend places in ``city`` and ``category`` using SQL filters, then rank by
    an adjustable score: better rating and lower price relative to a budget
    reference both help.

    ``max_price`` / ``min_rating`` filter in the database. ``price_budget`` sets
    the reference for price scoring (cheaper vs that budget scores higher); if
    omitted, ``max_price`` is used when set, otherwise the highest candidate price.

    ``rating_weight`` / ``price_weight`` control the blend (defaults balance both).
    Returns the top ``limit`` places by score (ties: higher rating, then name).
    """
    candidates = get_places_filtered(
        city=city,
        category=category,
        max_price=max_price,
        min_rating=min_rating,
        sort_by="rating",
        descending=True,
        limit=None,
    )
    if not candidates:
        return []

    pref = _price_reference(candidates, max_price, price_budget)
    ranked = sorted(
        candidates,
        key=lambda p: _recommendation_sort_key(
            p,
            price_reference=pref,
            rating_cap=rating_cap,
            rating_weight=rating_weight,
            price_weight=price_weight,
        ),
    )
    return ranked[:limit]


def calculate_daily_budget(total_budget: float, days: int) -> float:
    """
    Split `total_budget` evenly across `days`.

    Raises:
        ValueError: if ``days < 1`` or ``total_budget`` is negative.
    """
    if days < 1:
        raise ValueError("days must be at least 1")
    if total_budget < 0:
        raise ValueError("total_budget must be non-negative")
    return total_budget / days


def can_add_place(
    current_total: float,
    place_price: float,
    daily_budget: float,
) -> bool:
    """
    Return True if adding ``place_price`` to ``current_total`` stays within
    ``daily_budget`` (inclusive).
    """
    return current_total + place_price <= daily_budget


def _dedupe_places(pool: List[Place]) -> List[Place]:
    seen: Set[Place] = set()
    out: List[Place] = []
    for p in pool:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _median_price(places: List[Place]) -> float:
    if not places:
        return 0.0
    prices = sorted(p.price for p in places)
    n = len(prices)
    mid = n // 2
    if n % 2 == 1:
        return float(prices[mid])
    return (prices[mid - 1] + prices[mid]) / 2.0


def _prefer_cheap_next(
    picked: List[Place], median_price: float, rng: random.Random
) -> bool:
    """Steer the next pick toward cheaper or pricier options for balance."""
    if not picked:
        return rng.choice((True, False))
    above = sum(1 for p in picked if p.price > median_price)
    below = sum(1 for p in picked if p.price <= median_price)
    if above > below:
        return True
    if below > above:
        return False
    return rng.choice((True, False))


def _sort_by_rating(candidates: List[Place]) -> List[Place]:
    return sorted(candidates, key=lambda p: (-p.rating, p.name.lower()))


def _pick_high_rated_random_top(
    candidates: List[Place], rng: random.Random, top_k: int = _TOP_K_RANDOM
) -> Optional[Place]:
    if not candidates:
        return None
    ranked = _sort_by_rating(candidates)
    k = min(top_k, len(ranked))
    return rng.choice(ranked[:k])


def _pick_balanced_high_rated(
    candidates: List[Place],
    median_price: float,
    prefer_cheap: bool,
    rng: random.Random,
    top_k: int = _TOP_K_RANDOM,
) -> Optional[Place]:
    """
    Prefer high ratings; randomly choose among the top few.
    When balancing, favour the cheap or pricey band (still sorted by rating inside it).
    """
    if not candidates:
        return None
    ranked = _sort_by_rating(candidates)
    cheap = [p for p in ranked if p.price <= median_price]
    pricey = [p for p in ranked if p.price > median_price]

    if prefer_cheap:
        segment = cheap if cheap else ranked
    else:
        segment = pricey if pricey else ranked

    k = min(top_k, len(segment))
    return rng.choice(segment[:k])


def _build_day_places(
    activity_pool: List[Place],
    used: Set[Place],
    daily_limit: float,
    median_price: float,
    rng: random.Random,
) -> List[Place]:
    picked: List[Place] = []
    spent = 0.0
    categories_today: Set[str] = set()

    def affordable_subset(cands: List[Place]) -> List[Place]:
        return [p for p in cands if p not in used and spent + p.price <= daily_limit]

    all_categories = list({p.category for p in activity_pool})
    shuffled_cats = list(all_categories)
    rng.shuffle(shuffled_cats)

    # Phase 1 — at most one pick per category until we have enough distinct types
    for cat in shuffled_cats:
        if len(categories_today) >= _MIN_DISTINCT_CATEGORIES_PER_DAY:
            break
        if cat in categories_today:
            continue
        cands = affordable_subset([p for p in activity_pool if p.category == cat])
        if not cands:
            continue
        prefer = _prefer_cheap_next(picked, median_price, rng)
        choice = _pick_balanced_high_rated(cands, median_price, prefer, rng)
        if choice is None:
            continue
        picked.append(choice)
        used.add(choice)
        spent += choice.price
        categories_today.add(cat)

    # Phase 2 — still short on category diversity: force a new category if possible
    while len(categories_today) < _MIN_DISTINCT_CATEGORIES_PER_DAY:
        remaining = [c for c in all_categories if c not in categories_today]
        rng.shuffle(remaining)
        progressed = False
        for cat in remaining:
            cands = affordable_subset([p for p in activity_pool if p.category == cat])
            if not cands:
                continue
            prefer = _prefer_cheap_next(picked, median_price, rng)
            choice = _pick_balanced_high_rated(cands, median_price, prefer, rng)
            if choice is None:
                continue
            picked.append(choice)
            used.add(choice)
            spent += choice.price
            categories_today.add(cat)
            progressed = True
            break
        if not progressed:
            break

    # Phase 3 — grow the day to 3–4 stops (extra stops may repeat categories)
    target_total = rng.randint(3, 4)
    while len(picked) < target_total:
        cands = affordable_subset(list(activity_pool))
        if not cands:
            break
        prefer = _prefer_cheap_next(picked, median_price, rng)
        choice = _pick_balanced_high_rated(cands, median_price, prefer, rng)
        if choice is None:
            choice = _pick_high_rated_random_top(cands, rng)
        if choice is None:
            break
        picked.append(choice)
        used.add(choice)
        spent += choice.price

    return picked


def _split_days(number_of_days: int, num_cities: int) -> List[int]:
    """Distribute days as evenly as possible; extra days go to earlier cities."""
    base, extra = divmod(number_of_days, num_cities)
    return [base + (1 if i < extra else 0) for i in range(num_cities)]


def generate_itinerary(
    cities: List[str],
    total_budget: float,
    number_of_days: int,
) -> List[ItineraryDay]:
    """
    Build one ``ItineraryDay`` per day, keeping each city's days together.

    Days are divided evenly across cities (extra days go to the first city).
    All places on a given day belong to a single city — no cross-city mixing.
    No place is repeated across the entire trip. Each day targets at least
    three different categories and 3–4 stops within the daily budget share.
    Hotels are excluded from day plans when other activities exist.
    Each returned ``ItineraryDay`` has a ``.city`` attribute for display.
    """
    if not cities:
        raise ValueError("cities must be non-empty")

    # Deduplicate city list while preserving order
    seen_cities: Set[str] = set()
    unique_cities: List[str] = []
    for c in cities:
        if c not in seen_cities:
            seen_cities.add(c)
            unique_cities.append(c)

    rng = random.Random()
    daily_limit = calculate_daily_budget(total_budget, number_of_days)

    # Build a per-city activity pool (exclude hotels unless that is all there is)
    city_pools: dict = {}
    for city in unique_cities:
        city_places = _dedupe_places(get_places_by_city(city))
        activity = [p for p in city_places if p.category != "hotel"]
        city_pools[city] = activity if activity else city_places

    days_per_city = _split_days(number_of_days, len(unique_cities))

    # One shared used-set so no place repeats across the whole trip
    used: Set[Place] = set()
    itinerary: List[ItineraryDay] = []
    day_number = 1

    for city, num_days in zip(unique_cities, days_per_city):
        pool = city_pools[city]
        median_price = _median_price(pool)
        for _ in range(num_days):
            day_places = _build_day_places(
                pool, used, daily_limit, median_price, rng
            )
            day = ItineraryDay(day_number=day_number, places=day_places)
            day.city = city  # type: ignore[attr-defined]
            itinerary.append(day)
            day_number += 1

    return itinerary
