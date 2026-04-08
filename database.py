"""SQLite access for the travel planner — returns `Place` instances from `models`."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Literal, Optional

SortKey = Literal["rating", "price"]

from models import Place


class DatabaseError(Exception):
    """Raised when the database cannot be read or returned rows are invalid."""


def _db_path() -> Path:
    return Path(__file__).resolve().parent / "travel.db"


def _row_to_place(row: tuple) -> Place:
    try:
        name, city, category, price, rating = row
        return Place(
            name=str(name),
            city=str(city),
            category=str(category),
            price=int(price),
            rating=float(rating),
        )
    except (TypeError, ValueError) as exc:
        raise DatabaseError(f"Invalid place row: {row!r}") from exc


def connect_db() -> sqlite3.Connection:
    """Open a connection to `travel.db` next to this module."""
    path = _db_path()
    try:
        return sqlite3.connect(path)
    except sqlite3.Error as exc:
        raise DatabaseError(f"Could not connect to database: {path}") from exc


def get_all_places() -> List[Place]:
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = connect_db()
        cur = conn.execute(
            """
            SELECT name, city, category, price, rating
            FROM places
            ORDER BY id
            """
        )
        return [_row_to_place(tuple(row)) for row in cur.fetchall()]
    except DatabaseError:
        raise
    except sqlite3.Error as exc:
        raise DatabaseError("Failed to load all places") from exc
    finally:
        if conn is not None:
            conn.close()


def get_places_by_city(city: str) -> List[Place]:
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = connect_db()
        cur = conn.execute(
            """
            SELECT name, city, category, price, rating
            FROM places
            WHERE city = ?
            ORDER BY id
            """,
            (city,),
        )
        return [_row_to_place(tuple(row)) for row in cur.fetchall()]
    except DatabaseError:
        raise
    except sqlite3.Error as exc:
        raise DatabaseError(f"Failed to load places for city: {city!r}") from exc
    finally:
        if conn is not None:
            conn.close()


def get_places_by_category(category: str) -> List[Place]:
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = connect_db()
        cur = conn.execute(
            """
            SELECT name, city, category, price, rating
            FROM places
            WHERE category = ?
            ORDER BY id
            """,
            (category,),
        )
        return [_row_to_place(tuple(row)) for row in cur.fetchall()]
    except DatabaseError:
        raise
    except sqlite3.Error as exc:
        raise DatabaseError(f"Failed to load places for category: {category!r}") from exc
    finally:
        if conn is not None:
            conn.close()


def get_places_by_city_and_category(city: str, category: str) -> List[Place]:
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = connect_db()
        cur = conn.execute(
            """
            SELECT name, city, category, price, rating
            FROM places
            WHERE city = ? AND category = ?
            ORDER BY id
            """,
            (city, category),
        )
        return [_row_to_place(tuple(row)) for row in cur.fetchall()]
    except DatabaseError:
        raise
    except sqlite3.Error as exc:
        raise DatabaseError(
            f"Failed to load places for city={city!r} and category={category!r}"
        ) from exc
    finally:
        if conn is not None:
            conn.close()


def get_places_filtered(
    *,
    city: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_rating: Optional[float] = None,
    sort_by: SortKey = "rating",
    descending: bool = True,
    limit: Optional[int] = None,
) -> List[Place]:
    """
    Query places with optional filters and SQL ``ORDER BY`` (rating or price).

    ``sort_by`` must be ``\"rating\"`` or ``\"price\"``. Secondary sort is name
    (case-insensitive) ascending for stable results.
    """
    if sort_by not in ("rating", "price"):
        raise ValueError("sort_by must be 'rating' or 'price'")
    if limit is not None and limit < 1:
        raise ValueError("limit must be at least 1")

    clauses: List[str] = ["1 = 1"]
    params: List[object] = []

    if city is not None:
        clauses.append("city = ?")
        params.append(city)
    if category is not None:
        clauses.append("category = ?")
        params.append(category)
    if min_price is not None:
        clauses.append("price >= ?")
        params.append(min_price)
    if max_price is not None:
        clauses.append("price <= ?")
        params.append(max_price)
    if min_rating is not None:
        clauses.append("rating >= ?")
        params.append(min_rating)

    where_sql = " AND ".join(clauses)
    order_col = "rating" if sort_by == "rating" else "price"
    direction = "DESC" if descending else "ASC"
    sql = f"""
        SELECT name, city, category, price, rating
        FROM places
        WHERE {where_sql}
        ORDER BY {order_col} {direction}, name COLLATE NOCASE ASC
    """
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)

    conn: Optional[sqlite3.Connection] = None
    try:
        conn = connect_db()
        cur = conn.execute(sql, params)
        return [_row_to_place(tuple(row)) for row in cur.fetchall()]
    except DatabaseError:
        raise
    except sqlite3.Error as exc:
        raise DatabaseError("Failed to load filtered places") from exc
    finally:
        if conn is not None:
            conn.close()
