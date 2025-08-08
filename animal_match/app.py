from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import random
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            gender TEXT,
            grade TEXT,
            animal TEXT,
            intro TEXT,
            matched INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1 TEXT,
            user2 TEXT,
            animal TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    gender = request.form["gender"]
    grade = request.form["grade"]
    animal = request.form["animal"]
    intro = request.form["intro"]

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (name, gender, grade, animal, intro) VALUES (?, ?, ?, ?, ?)", 
              (name, gender, grade, animal, intro))
    conn.commit()

    c.execute("SELECT id FROM users WHERE name=? AND gender=? AND grade=? AND animal=? AND intro=? ORDER BY id DESC", 
              (name, gender, grade, animal, intro))
    user = c.fetchone()
    conn.close()

    session["user_id"] = user[0]
    return redirect("/loading")

@app.route("/loading")
def loading():
    return render_template("loading.html")

@app.route("/result")
def result():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/")

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()

    c.execute("SELECT * FROM users WHERE gender != ? AND animal = ? AND matched = 0 AND id != ?", 
              (user[2], user[4], user_id))
    candidates = c.fetchall()

    match = None
    if candidates:
        match = random.choice(candidates)
        c.execute("UPDATE users SET matched = 1 WHERE id IN (?, ?)", (user_id, match[0]))
        c.execute("INSERT INTO matches (user1, user2, animal) VALUES (?, ?, ?)", (user[1], match[1], user[4]))
        conn.commit()

    conn.close()

    user_dict = {
        'name': user[1], 'gender': user[2], 'grade': user[3], 'animal': user[4], 'intro': user[5]
    }

    match_dict = None
    if match:
        match_dict = {
            'name': match[1], 'gender': match[2], 'grade': match[3], 'animal': match[4], 'intro': match[5]
        }

    return render_template("result.html", user=user_dict, match=match_dict)

@app.route("/admin")
def admin():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    c.execute("SELECT * FROM matches")
    matches = c.fetchall()
    conn.close()
    return render_template("admin.html", users=users, matches=matches)

@app.route("/reset", methods=["POST"])
def reset():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("DELETE FROM users")
    c.execute("DELETE FROM matches")
    conn.commit()
    conn.close()
    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)
