"""Register, login, logout, change password."""

from __future__ import annotations

import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import db
from http_helpers import form_error, form_redirect


def register_auth_routes(app: Flask) -> None:
    @app.route("/register")
    def register():
        return render_template("register.html")

    @app.route("/create", methods=["POST"])
    def create():
        username = request.form.get("username", "").strip()
        password1 = request.form.get("password1", "")
        password2 = request.form.get("password2", "")
        if not username:
            return form_error("Käyttäjätunnus on pakollinen", 400)
        if not password1.strip():
            return form_error("Salasana on pakollinen", 400)
        if password1 != password2:
            return form_error("Salasanat eivät täsmää", 400)
        password_hash = generate_password_hash(password1)

        try:
            sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
            db.execute(sql, [username, password_hash])
        except sqlite3.IntegrityError:
            return form_error("Käyttäjätunnus on jo käytössä", 400)

        return form_redirect("/")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password.strip():
            return form_error("Virheellinen käyttäjätunnus tai salasana", 400)

        sql = "SELECT password_hash FROM users WHERE username = ?"
        found = db.query(sql, [username])
        if not found:
            return form_error("Virheellinen käyttäjätunnus tai salasana", 400)
        password_hash = found[0]["password_hash"]

        if check_password_hash(password_hash, password):
            session["username"] = username
            return form_redirect("/")

        return form_error("Virheellinen käyttäjätunnus tai salasana", 400)

    @app.route("/change_password", methods=["GET", "POST"])
    def change_password():
        if "username" not in session:
            return redirect(url_for("login"))
        username = session["username"]
        if request.method == "GET":
            return render_template("change_password.html")

        current_password = request.form.get("current_password", "")
        password1 = request.form.get("password1", "")
        password2 = request.form.get("password2", "")
        if not current_password.strip():
            return form_error("Nykyinen salasana puuttuu", 400)
        if not password1.strip():
            return form_error("Uusi salasana on pakollinen", 400)
        if password1 != password2:
            return form_error("Uudet salasanat eivät täsmää", 400)

        rows = db.query(
            "SELECT id, password_hash FROM users WHERE username = ?",
            [username],
        )
        if not rows:
            return form_error("Käyttäjää ei löydy", 400)

        if not check_password_hash(rows[0]["password_hash"], current_password):
            return form_error("Nykyinen salasana on väärä", 400)

        new_hash = generate_password_hash(password1)
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            [new_hash, rows[0]["id"]],
        )
        return form_redirect(url_for("profile"))

    @app.route("/logout")
    def logout():
        session.pop("username", None)
        return redirect("/")
