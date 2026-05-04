"""Flask application entry point."""

from __future__ import annotations

from flask import Flask

import config
from categories import register_category_jinja
from csrf import register_csrf
from error_handlers import register_error_handlers
from queries import register_query_jinja
from routes_auth import register_auth_routes
from routes_bookings import register_booking_routes
from routes_main import register_main_routes


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = config.secret_key
    register_csrf(app)
    register_query_jinja(app)
    register_category_jinja(app)
    register_error_handlers(app)
    register_main_routes(app)
    register_auth_routes(app)
    register_booking_routes(app)
    return app


app = create_app()
