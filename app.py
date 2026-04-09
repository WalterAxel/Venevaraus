import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import db
import config
import datetime


app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/new_reservation")
def new_reservation():
    return render_template("new_reservation.html")

@app.route("/create_reservation", methods=["POST"])
def create_reservation():
    title = request.form["title"]
    description = request.form["description"]
    start_date = request.form["reservation_start"]
    end_date = request.form["reservation_end"]
    user_id = db.execute("SELECT id FROM users WHERE username = ?", [session["username"]])
    if start_date > end_date:
        return "VIRHE: Aloituspäivän pitää olla ennen lopetuspäivää"
    elif title == "":
        return "VIRHE: Varauksen otsikko puuttuu"
    
    try:
        sql = "INSERT INTO reservations (title, description, start_date, end_date, user_id) VALUES (?, ?, ?, ?, ?)"
        db.execute(sql, [title, description, start_date, end_date, user_id])
    except sqlite3.IntegrityError:
        return "VIRHE: Varaus epäonnistui"

    return "Varaus tehty"

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

    return "Tunnus luotu"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
    
        sql = "SELECT password_hash FROM users WHERE username = ?"
        password_hash = db.query(sql, [username])[0][0]

        if check_password_hash(password_hash, password):
            session["username"] = username
            return redirect("/")
        else:
            return "VIRHE: väärä tunnus tai salasana"

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")


