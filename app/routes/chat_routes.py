# app/routes/chat_routes.py
from flask import Blueprint, request, jsonify, session
import sqlite3
import time
from app.utils import login_required

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/join', methods=['POST'])
@login_required
def join():
    data = request.get_json()
    circle_id = data['circle_id']
    username = session['user_name']
    # Handle any server-side logic if necessary
    return jsonify({'message': f'{username} has joined the chat.'}), 200

@chat_bp.route('/leave', methods=['POST'])
@login_required
def leave():
    data = request.get_json()
    circle_id = data['circle_id']
    username = session['user_name']
    # Handle any server-side logic if necessary
    return jsonify({'message': f'{username} has left the chat.'}), 200

@chat_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    circle_id = data['circle_id']
    username = session['user_name']
    message = data['message']
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages2 (circle_id, username, message, timestamp) VALUES (?, ?, ?, ?)",
              (circle_id, username, message, timestamp))
    conn.commit()
    conn.close()

    # Clients will fetch new messages via the polling endpoint
    return jsonify({'status': 'success'}), 200

@chat_bp.route('/get_messages', methods=['GET'])
@login_required
def get_messages():
    circle_id = request.args.get('circle_id')
    last_message_id = request.args.get('last_message_id', 0, type=int)

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("""
        SELECT id, circle_id, username, message, timestamp 
        FROM messages2 
        WHERE circle_id = ? AND id > ? 
        ORDER BY timestamp ASC
    """, (circle_id, last_message_id))
    messages = c.fetchall()
    conn.close()

    messages_list = []
    for msg in messages:
        messages_list.append({
            'id': msg[0],
            'circle_id': msg[1],
            'username': msg[2],
            'message': msg[3],
            'timestamp': msg[4]
        })

    return jsonify({'messages': messages_list}), 200
