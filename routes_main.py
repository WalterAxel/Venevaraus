"""Public pages: home, announcements list, profile, day view."""

from __future__ import annotations

from flask import Flask, abort, redirect, render_template, session, url_for

from categories import split_reservations_by_category
from queries import (
    get_calendar_reservations,
    get_profile_user,
    get_reservations_for_calendar_day,
    get_user_reservations,
)


def register_main_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        return render_template("index.html", reservations=get_calendar_reservations())

    @app.route("/announcements")
    def announcements():
        all_items = get_calendar_reservations()
        bookings, fault_reports = split_reservations_by_category(all_items)
        return render_template(
            "announcements.html",
            reservations=all_items,
            bookings=bookings,
            fault_reports=fault_reports,
        )

    @app.route("/profile")
    def profile():
        if "username" not in session:
            return redirect(url_for("login"))
        user_row = get_profile_user(session["username"])
        if user_row is None:
            return redirect(url_for("logout"))
        reservations = get_user_reservations(user_row["id"])
        return render_template(
            "profile.html",
            user=user_row,
            reservations=reservations,
        )

    @app.route("/reservations/day/<date_str>")
    def reservations_day(date_str):
        if len(date_str) != 10 or date_str[4] != "-" or date_str[7] != "-":
            abort(404)
        items = get_reservations_for_calendar_day(date_str)
        return render_template(
            "reservations_day.html", date_label=date_str, reservations=items
        )
