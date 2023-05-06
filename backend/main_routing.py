from flask import render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash
import backend.db as db
from backend.config import app


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        if db.getUser(username):
            return "Username already taken"

        password = request.form["password"]
        email = request.form['email']
        db.insertUser(username, email, password)

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = db.getUser(username)

        if user and check_password_hash(user["password"], password):
            session["username"] = username
            db.updateLastVisit(username)
            return redirect(url_for("index"))

        return "Invalid username/password"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))