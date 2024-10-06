# app/routes/main_routes.py
from flask import Blueprint, render_template, session, request, jsonify
import sqlite3
from app.utils import login_required
import openai
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template("logged_in_home.html")

@main_bp.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if 'conversation' not in session:
        session['conversation'] = []

    if request.method == 'POST':
        data = request.get_json()
        user_input = data.get('user_input', '').strip()
        # Append the user's message to the conversation
        session['conversation'].append({"role": "user", "content": user_input})
        openai.api_key = os.getenv('OPENAI_API_KEY')

        try:
            # OpenAI API call using the updated ChatCompletion endpoint
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Or "gpt-4" if you have access
                messages=[
                    {"role": "system", "content": "You are an expert farming assistant."},
                    *session['conversation'],
                ],
                max_tokens=150,
                temperature=0.7,
            )

            ai_response = response['choices'][0]['message']['content'].strip()
            # Append the assistant's response to the conversation
            session['conversation'].append({"role": "assistant", "content": ai_response})
        except Exception as e:
            print(f"OpenAI API error: {e}")
            ai_response = "Sorry, I'm having trouble accessing the AI service at the moment."
            session['conversation'].append({"role": "assistant", "content": ai_response})

        # Return the assistant's response as JSON
        return jsonify({'assistant_response': ai_response})

    else:
        return render_template('chat.html')

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
