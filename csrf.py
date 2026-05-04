"""Session CSRF tokens and POST validation."""

from __future__ import annotations

import secrets

from flask import Flask, jsonify, request, session

from http_helpers import error_page, forms_want_json


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def csrf_error_response():
    msg = (
        "Istunto vanhentui tai lomake ei ole kelvollinen. "
        "Lataa sivu ja yritä uudelleen."
    )
    if forms_want_json():
        return jsonify(error=msg), 400
    return error_page(f"VIRHE: {msg}", 400)


def register_csrf(app: Flask) -> None:
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def csrf_protect():
        if request.method != "POST":
            return None
        expected = session.get("csrf_token")
        sent = request.form.get("csrf_token")
        if not expected or not sent or not secrets.compare_digest(expected, sent):
            return csrf_error_response()
        return None
