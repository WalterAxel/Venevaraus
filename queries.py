"""SQLite reads for reservations and users."""

from __future__ import annotations

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


def to_datetime_local(value):
    if not value:
        return ""
    s = str(value).strip().replace(" ", "T")
    return s[:16] if len(s) >= 16 else s


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
