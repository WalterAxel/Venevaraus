"""Create, view, update, delete reservations."""

from __future__ import annotations

from flask import Flask, abort, redirect, render_template, request, session, url_for

import db
from categories import parse_category
from http_helpers import form_error, form_login_required_redirect, form_redirect
from queries import (
    get_calendar_reservations,
    get_reservation,
    normalize_reservation_date,
    to_date_input,
)


def register_booking_routes(app: Flask) -> None:
    @app.route("/new_reservation")
    def new_reservation():
        if "username" not in session:
            return redirect(url_for("login"))
        return render_template(
            "new_reservation.html", reservations=get_calendar_reservations()
        )

    @app.route("/create_reservation", methods=["POST"])
    def create_reservation():
        if "username" not in session:
            return form_login_required_redirect()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "")
        start_date = normalize_reservation_date(request.form.get("reservation_start", ""))
        end_date = normalize_reservation_date(request.form.get("reservation_end", ""))
        category = parse_category(request.form.get("category"))
        rows = db.query("SELECT id FROM users WHERE username = ?", [session["username"]])
        if not rows:
            return form_error("Käyttäjää ei löydy", 400)
        user_id = rows[0]["id"]
        if not start_date or not end_date:
            return form_error("Aloitus- ja lopetuspäivä ovat pakollisia", 400)
        if start_date > end_date:
            return form_error("Aloituspäivän täytyy olla ennen tai sama kuin lopetuspäivä", 400)
        if not title:
            return form_error("Otsikko on pakollinen", 400)

        sql = """
        INSERT INTO reservations
            (title, description, start_date, end_date, category, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        db.execute(sql, [title, description, start_date, end_date, category, user_id])

        return form_redirect("/")

    @app.route("/reservation/<int:reservation_id>")
    def view_reservation(reservation_id):
        row = get_reservation(reservation_id)
        if row is None:
            abort(404)
        is_owner = session.get("username") == row["username"]
        return render_template(
            "reservation.html",
            reservation=row,
            is_owner=is_owner,
            start_date_input=to_date_input(row["start_date"]),
            end_date_input=to_date_input(row["end_date"]),
        )

    @app.route("/reservation/<int:reservation_id>/edit", methods=["POST"])
    def edit_reservation(reservation_id):
        if "username" not in session:
            return form_login_required_redirect()
        row = get_reservation(reservation_id)
        if row is None:
            abort(404)
        if row["username"] != session["username"]:
            return form_error("Voit muokata vain omia ilmoituksiasi", 403)
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "")
        start_date = normalize_reservation_date(request.form.get("reservation_start", ""))
        end_date = normalize_reservation_date(request.form.get("reservation_end", ""))
        category = parse_category(request.form.get("category"))
        if not title:
            return form_error("Otsikko on pakollinen", 400)
        if not start_date or not end_date:
            return form_error("Aloitus- ja lopetuspäivä ovat pakollisia", 400)
        if start_date > end_date:
            return form_error("Aloituspäivän täytyy olla ennen tai sama kuin lopetuspäivä", 400)
        db.execute(
            """
            UPDATE reservations
            SET title = ?, description = ?, start_date = ?, end_date = ?, category = ?
            WHERE id = ?
            """,
            [title, description, start_date, end_date, category, reservation_id],
        )
        return form_redirect(url_for("view_reservation", reservation_id=reservation_id))

    @app.route("/reservation/<int:reservation_id>/delete", methods=["POST"])
    def delete_reservation(reservation_id):
        if "username" not in session:
            return form_login_required_redirect()
        row = get_reservation(reservation_id)
        if row is None:
            abort(404)
        if row["username"] != session["username"]:
            return form_error("Voit poistaa vain omia ilmoituksiasi", 403)
        db.execute("DELETE FROM reservations WHERE id = ?", [reservation_id])
        return form_redirect("/")
