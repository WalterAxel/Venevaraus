"""SQLite reads for reservations and users."""

from __future__ import annotations

from datetime import datetime

from flask import Flask

import db
from categories import category_label_fn, parse_category


def get_calendar_reservations():
    rows = db.query(
        """
        SELECT r.id AS reservation_id, r.title, r.start_date, r.end_date,
               r.category, u.username
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.start_date
        """
    )
    return [
        {
            "id": row["reservation_id"],
            "title": row["title"],
            "start": row["start_date"],
            "end": row["end_date"],
            "username": row["username"],
            "category": parse_category(row["category"]),
            "category_display": category_label_fn(row["category"]),
        }
        for row in rows
    ]


def _parse_date_part(value):
    if not value:
        return None
    s = str(value).strip().replace(" ", "T")
    part = s[:10]
    try:
        return datetime.strptime(part, "%Y-%m-%d").date()
    except ValueError:
        return None


def normalize_reservation_date(raw):
    """Return YYYY-MM-DD for storing reservation bounds, or "" if invalid."""
    d = _parse_date_part(raw)
    return d.isoformat() if d else ""


def to_date_input(value):
    """Value for HTML date inputs (YYYY-MM-DD)."""
    return normalize_reservation_date(value)


def format_display_date(value):
    """Format as DD.MM.YYYY for templates."""
    d = _parse_date_part(value)
    if d is None:
        return (str(value).strip() if value else "") or ""
    return f"{d.day:02d}.{d.month:02d}.{d.year}"


def get_reservation(reservation_id):
    rows = db.query(
        """
        SELECT r.id, r.title, r.description, r.start_date, r.end_date, r.category,
               r.user_id, u.username
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        WHERE r.id = ?
        """,
        [reservation_id],
    )
    if not rows:
        return None
    row = dict(rows[0])
    row["category"] = parse_category(row["category"])
    return row


def get_profile_user(username):
    rows = db.query(
        "SELECT id, username FROM users WHERE username = ?",
        [username],
    )
    return rows[0] if rows else None


def get_user_reservations(user_id):
    rows = db.query(
        """
        SELECT id, title, start_date, end_date, category
        FROM reservations
        WHERE user_id = ?
        ORDER BY start_date DESC
        """,
        [user_id],
    )
    out = []
    for row in rows:
        d = dict(row)
        d["category"] = parse_category(d["category"])
        out.append(d)
    return out


def get_reservations_for_calendar_day(date_str):
    rows = db.query(
        """
        SELECT r.id AS reservation_id, r.title, r.start_date, r.end_date,
               r.category, u.username
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        WHERE date(?) BETWEEN date(r.start_date) AND date(r.end_date)
        ORDER BY r.start_date
        """,
        [date_str],
    )
    return [
        {
            "id": row["reservation_id"],
            "title": row["title"],
            "start": row["start_date"],
            "end": row["end_date"],
            "username": row["username"],
            "category": parse_category(row["category"]),
        }
        for row in rows
    ]


def register_query_jinja(app: Flask) -> None:
    app.jinja_env.filters["display_date"] = format_display_date
