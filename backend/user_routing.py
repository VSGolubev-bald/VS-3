from flask import render_template, request, redirect, session, url_for, send_file
import backend.db as db
from backend.config import app


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        username = request.form["username"]
        if db.getUser(username):
            return "Username already taken"

        password = request.form["password"]
        email = request.form['email']
        db.insertUser(username, email, password)

        return redirect(url_for("users"))

    return render_template("add_user.html")


@app.route('/users')
def users():
    currentUser = db.getUser(session['username'])
    usersList = db.getAllUsers()
    return render_template('users.html', users=usersList, user=currentUser)


@app.route('/delete_user/<user_name>', methods=['GET'])
def delete_user(user_name):
    db.deleteUser(user_name)
    return redirect(url_for('users'))


@app.route('/edit_user/<user_name>', methods=['GET', 'POST'])
def edit_user(user_name):
    if request.method == 'GET':
        user_to_edit = db.getUser(user_name)
        return render_template('edit_user.html', user=user_to_edit)

    if request.method == 'POST':
        role = request.form['role']
        db.setRole(user_name, int(role))
        return redirect(url_for('users'))

