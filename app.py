import sqlite3
from flask import Flask
from flask import abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import db
import config


app = Flask(__name__)
app.secret_key = config.secret_key


def get_calendar_reservations():
    rows = db.query(
        """
        SELECT r.id AS reservation_id, r.title, r.start_date, r.end_date, u.username
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
        SELECT r.id, r.title, r.description, r.start_date, r.end_date, r.user_id, u.username
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        WHERE r.id = ?
        """,
        [reservation_id],
    )
    return rows[0] if rows else None


@app.route("/")
def index():
    return render_template("index.html", reservations=get_calendar_reservations())

@app.route("/new_reservation")
def new_reservation():
    if "username" not in session:
        return redirect("/login")
    return render_template(
        "new_reservation.html", reservations=get_calendar_reservations()
    )

@app.route("/create_reservation", methods=["POST"])
def create_reservation():
    if "username" not in session:
        return redirect("/login")
    title = request.form["title"]
    description = request.form["description"]
    start_date = request.form["reservation_start"]
    end_date = request.form["reservation_end"]
    rows = db.query("SELECT id FROM users WHERE username = ?", [session["username"]])
    if not rows:
        return "VIRHE: käyttäjää ei löydy"
    user_id = rows[0]["id"]
    if start_date > end_date:
        return "VIRHE: Aloituspäivän pitää olla ennen lopetuspäivää"
    elif title == "":
        return "VIRHE: Varauksen otsikko puuttuu"
    
    try:
        sql = "INSERT INTO reservations (title, description, start_date, end_date, user_id) VALUES (?, ?, ?, ?, ?)"
        db.execute(sql, [title, description, start_date, end_date, user_id])
    except sqlite3.IntegrityError:
        return "VIRHE: Varaus epäonnistui"

    return redirect("/")

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
        SELECT r.id AS reservation_id, r.title, r.start_date, r.end_date, u.username
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
        }
        for row in rows
    ]
    return render_template(
        "reservations_day.html", date_label=date_str, reservations=items
    )


@app.route("/reservation/<int:reservation_id>/edit", methods=["POST"])
def edit_reservation(reservation_id):
    if "username" not in session:
        return redirect("/login")
    row = get_reservation(reservation_id)
    if row is None:
        abort(404)
    if row["username"] != session["username"]:
        return "VIRHE: voit muokata vain omia varauksiasi", 403
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "")
    start_date = request.form.get("reservation_start", "")
    end_date = request.form.get("reservation_end", "")
    if not title:
        return "VIRHE: Varauksen otsikko puuttuu"
    if start_date > end_date:
        return "VIRHE: Aloituspäivän pitää olla ennen lopetuspäivää"
    db.execute(
        """
        UPDATE reservations
        SET title = ?, description = ?, start_date = ?, end_date = ?
        WHERE id = ?
        """,
        [title, description, start_date, end_date, reservation_id],
    )
    return redirect(url_for("view_reservation", reservation_id=reservation_id))


@app.route("/reservation/<int:reservation_id>/delete", methods=["POST"])
def delete_reservation(reservation_id):
    if "username" not in session:
        return redirect("/login")
    row = get_reservation(reservation_id)
    if row is None:
        abort(404)
    if row["username"] != session["username"]:
        return "VIRHE: voit poistaa vain omia varauksiasi", 403
    db.execute("DELETE FROM reservations WHERE id = ?", [reservation_id])
    return redirect("/")

@app.route("/register") 
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        return "VIRHE: salasanat eivät ole samat"
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "VIRHE: tunnus on jo varattu"

    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
    
        sql = "SELECT password_hash FROM users WHERE username = ?"
        found = db.query(sql, [username])
        if not found:
            return "VIRHE: väärä tunnus tai salasana"
        password_hash = found[0][0]

        if check_password_hash(password_hash, password):
            session["username"] = username
            return redirect("/")
        else:
            return "VIRHE: väärä tunnus tai salasana"

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

