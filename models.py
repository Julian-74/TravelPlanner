"""Domain models for the travel planner application."""

from __future__ import annotations

from typing import Iterable, List, Optional


class Place:
    """A point of interest or venue on an itinerary."""

    def __init__(
        self,
        name: str,
        city: str,
        category: str,
        price: int,
        rating: float,
    ) -> None:
        self.name = name
        self.city = city
        self.category = category
        self.price = price
        self.rating = rating

    def __repr__(self) -> str:
        return (
            f"Place(name={self.name!r}, city={self.city!r}, "
            f"category={self.category!r}, price={self.price}, rating={self.rating})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Place):
            return NotImplemented
        return (
            self.name == other.name
            and self.city == other.city
            and self.category == other.category
            and self.price == other.price
            and self.rating == other.rating
        )

    def __hash__(self) -> int:
        return hash(
            (self.name, self.city, self.category, self.price, self.rating)
        )

    def summary(self) -> str:
        return f"{self.name} ({self.category}) — {self.price} · ★ {self.rating}"


class ItineraryDay:
    """One day of a trip: ordered places and their combined cost."""

    def __init__(
        self,
        day_number: int,
        places: Optional[Iterable[Place]] = None,
    ) -> None:
        if day_number < 1:
            raise ValueError("day_number must be >= 1")
        self.day_number = day_number
        self.places: List[Place] = list(places) if places else []

    @property
    def total_cost(self) -> int:
        return sum(p.price for p in self.places)

    def add_place(self, place: Place) -> None:
        self.places.append(place)

    def remove_place(self, place: Place) -> bool:
        try:
            self.places.remove(place)
            return True
        except ValueError:
            return False

    def clear_places(self) -> None:
        self.places.clear()

    def __repr__(self) -> str:
        return (
            f"ItineraryDay(day_number={self.day_number}, "
            f"places={self.places!r}, total_cost={self.total_cost})"
        )


class Trip:
    """A multi-day trip with cities, budget, and per-day itinerary."""

    def __init__(
        self,
        cities: Iterable[str],
        budget: float,
        number_of_days: int,
        itinerary: Optional[Iterable[ItineraryDay]] = None,
    ) -> None:
        if budget < 0:
            raise ValueError("budget must be non-negative")
        if number_of_days < 1:
            raise ValueError("number_of_days must be >= 1")
        self.cities = list(cities)
        self.budget = budget
        self.number_of_days = number_of_days
        if itinerary is not None:
            self.itinerary = list(itinerary)
            if len(self.itinerary) != number_of_days:
                raise ValueError(
                    "itinerary length must equal number_of_days "
                    f"({len(self.itinerary)} != {number_of_days})"
                )
        else:
            self.itinerary = self._empty_itinerary(number_of_days)

    @staticmethod
    def _empty_itinerary(days: int) -> List[ItineraryDay]:
        return [ItineraryDay(day_number=d) for d in range(1, days + 1)]

    @property
    def total_cost(self) -> int:
        return sum(day.total_cost for day in self.itinerary)

    @property
    def remaining_budget(self) -> int:
        return self.budget - self.total_cost

    def is_within_budget(self) -> bool:
        return self.total_cost <= self.budget

    def day(self, day_number: int) -> Optional[ItineraryDay]:
        for d in self.itinerary:
            if d.day_number == day_number:
                return d
        return None

    def add_place_to_day(self, day_number: int, place: Place) -> bool:
        d = self.day(day_number)
        if d is None:
            return False
        d.add_place(place)
        return True

    def set_itinerary(self, days: Iterable[ItineraryDay]) -> None:
        days_list = list(days)
        if len(days_list) != self.number_of_days:
            raise ValueError(
                "itinerary length must equal number_of_days "
                f"({len(days_list)} != {self.number_of_days})"
            )
        self.itinerary = days_list

    def __repr__(self) -> str:
        return (
            f"Trip(cities={self.cities!r}, budget={self.budget}, "
            f"number_of_days={self.number_of_days}, itinerary={self.itinerary!r})"
        )
