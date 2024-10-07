# app/routes/api_routes.py
from flask import Blueprint, jsonify, request
import sqlite3

api_bp = Blueprint('api', __name__)

@api_bp.route('/get_circles', methods=['GET'])
def get_circles():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM circles")
    circles = c.fetchall()
    conn.close()
    return jsonify([{'id': circle[0], 'lat': circle[1], 'lng': circle[2], 'radius': circle[3]} for circle in circles])

@api_bp.route('/add_circle', methods=['POST'])
def add_circle():
    data = request.get_json()
    lat = data['lat']
    lng = data['lng']
    radius = data['radius']

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO circles (lat, lng, radius) VALUES (?, ?, ?)", (lat, lng, radius))
    conn.commit()
    circle_id = c.lastrowid
    conn.close()

    return jsonify({'message': 'Circle added successfully', 'id': circle_id})

@api_bp.route('/get_chat_messages/<int:circle_id>', methods=['GET'])
def get_chat_messages(circle_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages2 WHERE circle_id = ? ORDER BY timestamp ASC", (circle_id,))
    messages = c.fetchall()
    conn.close()
    return jsonify([{'username': message[0], 'message': message[1], 'timestamp': message[2]} for message in messages])
