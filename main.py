from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from netCDF4 import Dataset
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
from flask_socketio import SocketIO, send, emit
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
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
@login_required
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

@app.route('/plot')
def plot():
    # Open the NC4 file
    nc_file = 'test.nc4'  # Replace with your NC4 file path
    dataset = Dataset(nc_file, 'r')

    # Access soil moisture data
    sm1 = dataset.variables['sm1'][:]  # Read the soil moisture data
    latitudes = dataset.variables['lat'][:]  # Read latitude data
    longitudes = dataset.variables['lon'][:]

    # Check for missing values and replace them with NaN
    sm1_masked = np.ma.masked_where(sm1 == dataset.variables['sm1']._FillValue, sm1)
    sm1_masked[sm1_masked < 0] = np.nan
   
    sm1_values = sm1_masked[0].flatten()  # Flatten the array
    latitudes = np.repeat(latitudes, len(longitudes))  # Repeat latitudes for each longitude
    longitudes = np.tile(longitudes, len(latitudes) // len(longitudes))  # Tile longitudes

    # Create a DataFrame for Plotly

    data = pd.DataFrame({
        'Latitude': latitudes,
        'Longitude': longitudes,
        'Soil Moisture': sm1_values
    })

    # Filter out NaN values
    data = data.dropna()

    # Create a scatter mapbox
    fig = px.scatter_mapbox(data, 
                             lat='Latitude', 
                             lon='Longitude', 
                             size='Soil Moisture',
                             color='Soil Moisture',
                             color_continuous_scale=px.colors.sequential.Viridis,
                             mapbox_style='carto-positron',
                             zoom=3,
                             title='Soil Moisture Map')

    # Generate the HTML for the plot
    plot_html = fig.to_html(full_html=False)

    return plot_html

@socketio.on('connect')
def handle_connect():
    # Send previous messages to newly connected clients
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages ORDER BY timestamp ASC")
    messages = c.fetchall()
    conn.close()
    for message in messages:
        emit('message', {'username': message[0], 'message': message[1], 'timestamp': message[2]})

@socketio.on('message')
def handle_message(msg):
    username = session['user_name']
    message = msg['message']
    print(f"{username}: {message}")

    # Save message to the database
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (username, message) VALUES (?, ?)", (username, message))
    conn.commit()
    conn.close()

    # Broadcast message to all clients
    send({'username': username, 'message': message, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, debug=True)