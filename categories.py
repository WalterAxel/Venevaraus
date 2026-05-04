"""Reservation category values, labels, and normalization."""

from __future__ import annotations

from flask import Flask

VALID_CATEGORIES = frozenset({"booking", "fault_report"})
CATEGORY_LABELS = {"booking": "Varaus", "fault_report": "Vikailmoitus"}
_LEGACY_CATEGORIES = {"varaus": "booking", "vikailmoitus": "fault_report"}
DEFAULT_CATEGORY = "booking"


def parse_category(raw):
    v = (raw or "").strip()
    v = _LEGACY_CATEGORIES.get(v, v)
    return v if v in VALID_CATEGORIES else DEFAULT_CATEGORY


def split_reservations_by_category(items):
    bookings = [r for r in items if parse_category(r["category"]) == "booking"]
    fault_reports = [r for r in items if parse_category(r["category"]) == "fault_report"]
    return bookings, fault_reports


def category_label_fn(value):
    return CATEGORY_LABELS[parse_category("" if value is None else value)]


def register_category_jinja(app: Flask) -> None:
    app.jinja_env.globals["category_label"] = category_label_fn
