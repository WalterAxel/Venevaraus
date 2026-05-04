"""Application-wide HTTP error rendering."""

from __future__ import annotations

from flask import Flask

from http_helpers import error_page


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def handle_not_found(_e):
        return error_page("VIRHE: Sivua ei löytynyt.", 404)

    @app.errorhandler(500)
    def handle_server_error(_e):
        return error_page(
            "VIRHE: Palvelimella tapahtui virhe. Yritä myöhemmin uudelleen.", 500
        )

    @app.errorhandler(405)
    def handle_method_not_allowed(_e):
        return error_page(
            "VIRHE: Tämä pyyntötapa ei ole sallittu tälle osoitteelle.", 405
        )
