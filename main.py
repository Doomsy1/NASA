from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from netCDF4 import Dataset
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import time
import numpy as np
import pandas as pd
import plotly.express as px

app = Flask(__name__)
app.secret_key = "winners"
socketio = SocketIO(app)

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS circles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lat REAL NOT NULL,
                    lng REAL NOT NULL,
                    radius REAL NOT NULL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    circle_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (circle_id) REFERENCES circles(id)
                )''')
    conn.commit()
    conn.close()

init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('You need to be logged in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    return render_template("logged_in_home.html")

@app.route('/forecast')
@login_required
def forecast():
    return render_template("forecast.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        confirm_email = request.form['confirm_email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if email != confirm_email:
            flash('Emails do not match. Please try again.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Insert user into the database
        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hashed_password))
            conn.commit()
            conn.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered. Please use a different email.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Verify user credentials
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['logged_in'] = True
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/farmer_discussion')
@login_required
def farmer_discussion():
    # Load previous messages from the database
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages ORDER BY timestamp ASC")
    messages = c.fetchall()
    conn.close()
    return render_template('farmer_discussion.html', username=session['user_name'], messages=messages)

@app.route('/get_circles', methods=['GET'])
def get_circles():
    # Fetch all circles from the database
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM circles")
    circles = c.fetchall()
    conn.close()
    return jsonify([{'id': circle[0], 'lat': circle[1], 'lng': circle[2], 'radius': circle[3]} for circle in circles])

@app.route('/add_circle', methods=['POST'])
def add_circle():
    data = request.get_json()
    lat = data['lat']
    lng = data['lng']
    radius = data['radius']

    # Insert new circle into the database
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO circles (lat, lng, radius) VALUES (?, ?, ?)", (lat, lng, radius))
    conn.commit()
    circle_id = c.lastrowid
    conn.close()

    return jsonify({'message': 'Circle added successfully', 'id': circle_id})

@app.route('/get_chat_messages/<int:circle_id>', methods=['GET'])
def get_chat_messages(circle_id):
    # Fetch messages for a specific circle
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages WHERE circle_id = ? ORDER BY timestamp ASC", (circle_id,))
    messages = c.fetchall()
    conn.close()
    return jsonify([{'username': message[0], 'message': message[1], 'timestamp': message[2]} for message in messages])

@socketio.on('join')
def on_join(data):
    circle_id = data['circle_id']
    username = data['username']
    room = f"circle_{circle_id}"
    join_room(room)
    send({'username': username, 'message': f'{username} has joined the chat.'}, to=room)

@socketio.on('leave')
def on_leave(data):
    circle_id = data['circle_id']
    username = data['username']
    room = f"circle_{circle_id}"
    leave_room(room)
    send({'username': username, 'message': f'{username} has left the chat.'}, to=room)

@socketio.on('message')
def handle_message(msg):
    circle_id = msg['circle_id']
    username = msg['username']
    message = msg['message']
    room = f"circle_{circle_id}"
    print(f"{username}: {message}")

    # Save message to the database
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (circle_id, username, message) VALUES (?, ?, ?)", (circle_id, username, message))
    conn.commit()
    conn.close()

    # Broadcast message to all clients in the same chatroom
    send({'circle_id': circle_id, 'username': username, 'message': message, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}, to=room)

if __name__ == "__main__":
    socketio.run(app, debug=True)