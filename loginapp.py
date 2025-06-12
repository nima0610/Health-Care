from flask import Flask, request, jsonify, render_template, redirect
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="healthcare11"
    )

# Redirect root URL to /login
@app.route('/')
def home():
    return redirect('/login')


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM user WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        if user:
            return jsonify({'status': 'success', 'role': 'user'})

        cursor.execute("SELECT * FROM doctor WHERE email = %s AND password = %s", (email, password))
        doctor = cursor.fetchone()

        if doctor:
            return jsonify({'status': 'success', 'role': 'doctor'})

        return jsonify({'status': 'fail', 'message': 'Invalid credentials'}), 401

    except Exception as e:
        print("Error:", e)
        return jsonify({'status': 'fail', 'message': 'Server error'}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, port=5002)
