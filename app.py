import secrets
import sqlite3
from flask import Flask
from flask import abort, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import db
import config


app = Flask(__name__)
app.secret_key = config.secret_key


def error_page(message, status_code=400):
    return render_template("error.html", message=message), status_code


def forms_want_json():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def form_error(message: str, status_code: int = 400):
    if forms_want_json():
        return jsonify(error=message), status_code
    return error_page(f"ERROR: {message}", status_code)


def form_redirect(location: str):
    if forms_want_json():
        return jsonify(redirect=location), 200
    return redirect(location)


def form_login_required_redirect():
    login_url = url_for("login")
    if forms_want_json():
        return jsonify(redirect=login_url), 401
    return redirect(login_url)


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


def _csrf_error_response():
    msg = (
        "Your session expired or the form was invalid. "
        "Refresh the page and try again."
    )
    if forms_want_json():
        return jsonify(error=msg), 400
    return error_page(f"ERROR: {msg}", 400)


@app.before_request
def csrf_protect():
    if request.method != "POST":
        return None
    expected = session.get("csrf_token")
    sent = request.form.get("csrf_token")
    if not expected or not sent or not secrets.compare_digest(expected, sent):
        return _csrf_error_response()
    return None


VALID_CATEGORIES = frozenset({"booking", "fault_report"})
CATEGORY_LABELS = {"booking": "Booking", "fault_report": "Fault report"}
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


app.jinja_env.globals["category_label"] = category_label_fn


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
    start_date = request.form.get("reservation_start", "")
    end_date = request.form.get("reservation_end", "")
    category = parse_category(request.form.get("category"))
    rows = db.query("SELECT id FROM users WHERE username = ?", [session["username"]])
    if not rows:
        return form_error("User not found", 400)
    user_id = rows[0]["id"]
    if not start_date or not end_date:
        return form_error("Start and end date and time are required", 400)
    if start_date > end_date:
        return form_error("Start must be before end", 400)
    if not title:
        return form_error("Title is required", 400)

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
        start_local=to_datetime_local(row["start_date"]),
        end_local=to_datetime_local(row["end_date"]),
    )


@app.route("/reservations/day/<date_str>")
def reservations_day(date_str):
    if len(date_str) != 10 or date_str[4] != "-" or date_str[7] != "-":
        abort(404)
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
    items = [
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
    return render_template(
        "reservations_day.html", date_label=date_str, reservations=items
    )


@app.route("/reservation/<int:reservation_id>/edit", methods=["POST"])
def edit_reservation(reservation_id):
    if "username" not in session:
        return form_login_required_redirect()
    row = get_reservation(reservation_id)
    if row is None:
        abort(404)
    if row["username"] != session["username"]:
        return form_error("You can only edit your own reservations", 403)
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "")
    start_date = request.form.get("reservation_start", "")
    end_date = request.form.get("reservation_end", "")
    category = parse_category(request.form.get("category"))
    if not title:
        return form_error("Title is required", 400)
    if not start_date or not end_date:
        return form_error("Start and end date and time are required", 400)
    if start_date > end_date:
        return form_error("Start must be before end", 400)
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
        return form_error("You can only delete your own reservations", 403)
    db.execute("DELETE FROM reservations WHERE id = ?", [reservation_id])
    return form_redirect("/")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/create", methods=["POST"])
def create():
    username = request.form.get("username", "").strip()
    password1 = request.form.get("password1", "")
    password2 = request.form.get("password2", "")
    if not username:
        return form_error("Username is required", 400)
    if password1 != password2:
        return form_error("Passwords do not match", 400)
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return form_error("Username is already taken", 400)

    return form_redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username:
            return form_error("Invalid username or password", 400)

        sql = "SELECT password_hash FROM users WHERE username = ?"
        found = db.query(sql, [username])
        if not found:
            return form_error("Invalid username or password", 400)
        password_hash = found[0]["password_hash"]

        if check_password_hash(password_hash, password):
            session["username"] = username
            return form_redirect("/")
        else:
            return form_error("Invalid username or password", 400)


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")


@app.errorhandler(404)
def handle_not_found(_e):
    return error_page("ERROR: Page not found.", 404)


@app.errorhandler(500)
def handle_server_error(_e):
    return error_page("ERROR: Something went wrong. Please try again later.", 500)


@app.errorhandler(405)
def handle_method_not_allowed(_e):
    return error_page("ERROR: Method not allowed for this URL.", 405)
