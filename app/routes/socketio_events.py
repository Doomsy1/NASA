# app/routes/socketio_events.py
from flask_socketio import join_room, leave_room, send
import sqlite3
import time
from app import socketio

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

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (circle_id, username, message) VALUES (?, ?, ?)", (circle_id, username, message))
    conn.commit()
    conn.close()

    send({'circle_id': circle_id, 'username': username, 'message': message, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}, to=room)
