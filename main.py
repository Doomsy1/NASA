from flask import *
# from werkzeug.security import generate_password_hash,check_password_hash
import sqlite3
import random
import time

app=Flask(__name__)
app.secret_key = "winners"
logged_in = False

@app.route('/')
def home():
    if logged_in:
        return render_template("logged_in_home.html")
    else:
        return render_template("logged_out_home.html")
    
@app.route('/forecast')
def forecast():
    if logged_in:
        return render_template("logged_in_home.html")
    else:
        return render_template("forecast.html")


if __name__ == "__main__":
    app.run()