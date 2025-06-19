from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="healthcare11"
    )


# 🔁 Redirect root to login
@app.route('/')
def home():
    return redirect('/login')


# ➕ Bridge Page
@app.route('/bridge.html')
def bridge():
    return render_template('bridge.html')


# ✅ Admin Page Display: doctors where is_approved = 0
@app.route('/admin')
def admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, specialization, contact FROM doctor WHERE is_approved = 0")
    doctors = cursor.fetchall()
     # Fetch all patients
    cursor.execute("SELECT id, name, email, password FROM user")
    patients = cursor.fetchall()
    print("Doctors fetched:", doctors)    # <-- debug output
    print("Patients fetched:", patients)  # <-- debug output
    cursor.close()
    conn.close()
    return render_template("adminpage.html", doctors=doctors, patients=patients)


# ✅ Approve doctor (set is_approved = 1)
@app.route('/approve/<int:doctor_id>', methods=['POST'])
def approve_doctor(doctor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE doctor SET is_approved = 1 WHERE id = %s", (doctor_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin'))


# ❌ Reject doctor (delete row)
@app.route('/reject/<int:doctor_id>', methods=['POST'])
def reject_doctor(doctor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM doctor WHERE id = %s", (doctor_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin'))


# ➕ Register Doctor
@app.route('/register_doctor', methods=['GET', 'POST'])
def register_doctor():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        specialization = request.form['specialization']
        contact = request.form['contact']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if email exists
        cursor.execute("SELECT * FROM doctor WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already exists for doctor.')
            cursor.close()
            conn.close()
            return redirect(url_for('register_doctor'))

        # Insert doctor
        cursor.execute(
            "INSERT INTO doctor (name, email, password, specialization, contact) VALUES (%s, %s, %s, %s, %s)",
            (name, email, password, specialization, contact)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash('Doctor registration successful! You can now log in.')
        return redirect(url_for('login'))

    return render_template('register_doctor.html')


@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == 'admin@1234' and password == '12345':
              return redirect(url_for('admin'))
        else:
            error = "Invalid credentials"
    return render_template('admin.html', error=error)


@app.route('/adminpage')
def adminpage():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all users from the user table
    cursor.execute("SELECT id, name, email, password FROM user")
    patients = cursor.fetchall()

    conn.close()

    return render_template('adminpage.html', patients=patients)


# ➕ Register Normal User
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if email exists
        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already exists.')
            cursor.close()
            conn.close()
            return redirect(url_for('register'))

        # Insert user
        cursor.execute(
            "INSERT INTO user (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))

    return render_template('register.html')


# 🔐 Login route
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

        # Check if user
        cursor.execute("SELECT * FROM user WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        if user:
            return jsonify({'status': 'success', 'role': 'user'})

        # Check if doctor
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


# 🚀 Run the app
if __name__ == '__main__':
    app.run(debug=True, port=5002)
