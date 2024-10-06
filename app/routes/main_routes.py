# app/routes/main_routes.py
from flask import Blueprint, render_template, session
import sqlite3
from app.utils import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template("logged_in_home.html")

@main_bp.route('/forecast')
@login_required
def forecast():
    return render_template("forecast.html")

@main_bp.route('/farmer_discussion')
@login_required
def farmer_discussion():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages ORDER BY timestamp ASC")
    messages = c.fetchall()
    conn.close()
    return render_template('farmer_discussion.html', username=session['user_name'], messages=messages)
