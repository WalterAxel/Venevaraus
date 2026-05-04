"""HTTP/HTML and JSON helpers for validation errors and redirects."""

from __future__ import annotations

from flask import jsonify, redirect, render_template, request, url_for


def error_page(message: str, status_code: int = 400):
    return render_template("error.html", message=message), status_code


def forms_want_json() -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def form_error(message: str, status_code: int = 400):
    if forms_want_json():
        return jsonify(error=message), status_code
    return error_page(f"VIRHE: {message}", status_code)


def form_redirect(location: str):
    if forms_want_json():
        return jsonify(redirect=location), 200
    return redirect(location)


def form_login_required_redirect():
    login_url = url_for("login")
    if forms_want_json():
        return jsonify(redirect=login_url), 401
    return redirect(login_url)
