import os
from flask import Flask, request, jsonify,render_template,url_for,redirect
import mysql.connector
from flask_bcrypt import Bcrypt
from mysql.connector import Error
from werkzeug.utils import secure_filename
from flask import send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_mysqldb import MySQL
from datetime import datetime
import uuid
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

CHAT_UPLOADS = os.path.join(os.getcwd(), 'chat_uploads')
os.makedirs(CHAT_UPLOADS, exist_ok=True)


@socketio.on('join')
def on_join(data):
    room = data['room']
    username = data['username']
    join_room(room)
    print(f"{username} joined room {room}")

@socketio.on('message')
def on_message(data):
    room = data['room']
    print(f"Message to room {room}: {data['message']}")
    emit('message', data, room=room)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Set your MySQL password
app.config['MYSQL_DB'] = 'healthcare11'

# File Upload Configuration
UPLOAD_FOLDER = 'static/uploads'
CHAT_UPLOADS = 'static/chat_uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directories if they don't exist
for folder in [UPLOAD_FOLDER, CHAT_UPLOADS]:
    if not os.path.exists(folder):
        os.makedirs(folder)

mysql = MySQL(app)
bcrypt = Bcrypt(app)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/signout')
def signout():
    return redirect("http://localhost:5002/")

@app.route('/get_specializations')
def get_specializations():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT specialization FROM doctor")
    specs = [row[0] for row in cur.fetchall()]
    cur.close()
    return jsonify({'specializations': specs})

@app.route('/get_doctors_by_specialization')
def get_doctors_by_specialization():
    specialization = request.args.get('specialization')
    cur = mysql.connection.cursor()
    cur.execute("SELECT name, email FROM doctor WHERE specialization = %s AND is_approved = 1",(specialization,))
    doctors = [{'name': row[0], 'email': row[1]} for row in cur.fetchall()]
    cur.close()
    return jsonify({'doctors': doctors})
# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'success': False,
        'message': 'Resource not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({
        'success': False,
        'message': 'File is too large. Maximum size is 16MB'
    }), 413

@app.route('/chat_uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(CHAT_UPLOADS, filename)

@app.route('/')
def first_index():
    return render_template('consult.html')

@app.route('/doctorpage')
def doctorpage():
    return render_template('doctorpage.html')

@app.route('/register')
def show_registrer():
    return render_template('registration.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        age = request.form.get('age')
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        role = request.form.get('role')

        # Validate required fields
        if not all([name, email, password, phone, role]):
            return jsonify({
                "status": "error",
                "message": "All required fields must be filled"
            }), 400

        # Create database connection
        cur = mysql.connection.cursor()
        
        # Check if email already exists in either user or doctor table
        cur.execute("SELECT email FROM user WHERE email = %s", (email,))
        user_exists = cur.fetchone()
        cur.execute("SELECT email FROM doctor WHERE email = %s", (email,))
        doctor_exists = cur.fetchone()
        
        if user_exists or doctor_exists:
            cur.close()
            return jsonify({
                "status": "error",
                "message": "Email already exists"
            }), 400

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        if role == 'user':
            # Insert user data
            cur.execute("""
            INSERT INTO user (name, email, password, phone, address, age, gender, dob)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, email, hashed_password, phone, address, age, gender, dob))

        elif role == 'doctor':
            # Handle doctor registration
            specialization = request.form.get('specialization')
            document_path = None
            
            # Handle document upload if provided
            if 'specialization_doc' in request.files:
                file = request.files['specialization_doc']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    document_path = f'doc_{datetime.now().strftime("%Y%m%d%H%M%S")}_{filename}'
                    file.save(os.path.join(UPLOAD_FOLDER, document_path))

            # Insert doctor data
            cur.execute("""
                INSERT INTO doctor (name, email, password, phone, address, specialization, document_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, email, hashed_password, phone, address, specialization, document_path))

        # Commit changes and close connection
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            "status": "success",
            "message": "Registration successful"
        }), 200
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Show login page (GET request)
@app.route("/login", methods=["GET"])
def show_login():
   return redirect("http://localhost:5005/")

# Handle login form via JavaScript (POST request)
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        role = data.get("role")

        if not all([email, password, role]):
            return jsonify({
                "status": "error", 
                "message": "All fields are required"
            }), 400

        # Create database connection
        cur = mysql.connection.cursor()
        
        # Check user based on role
        if role == "user":
            cur.execute("SELECT * FROM user WHERE email = %s", (email,))
        elif role == "doctor":
            cur.execute("SELECT * FROM doctor WHERE email = %s", (email,))
        else:
            cur.close()
            return jsonify({
                "status": "error", 
                "message": "Invalid role"
            }), 400

        user = cur.fetchone()
        cur.close()

        if user:
            # Get the password from the correct index based on your table structure
            stored_password = user[3]  # Assuming password is the 4th column
            
            if bcrypt.check_password_hash(stored_password, password):
                return jsonify({
                    "status": "success",
                    "role": role,
                    "user": {
                        "email": email,
                        "name": user[1]  # Assuming name is the 2nd column
                    }
                }), 200
            else:
                return jsonify({
                    "status": "error", 
                    "message": "Incorrect password"
                }), 401
        else:
            return jsonify({
                "status": "error", 
                "message": "User not found"
            }), 404

    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route('/mainpage')
def mainpage():
    return render_template('mainpage.html')

@app.route("/doctormainpage")
def doctor_main():
     return render_template('doctormainpage.html')

@app.route("/consult.html")
def consult():
    return render_template("consult.html")

@socketio.on('join')
def on_join(data):
    room = data['room']
    username = data['username']
    join_room(room)
    
    # Load chat history
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT sender_email, message, message_type, file_path, created_at 
        FROM chat_messages 
        WHERE room_id = %s 
        ORDER BY created_at DESC 
        LIMIT 50
    """, (room,))
    
    messages = cur.fetchall()
    cur.close()
    
    # Send chat history to the user
    for msg in reversed(messages):
        emit('message', {
            'username': msg[0],
            'message': msg[1],
            'type': msg[2],
            'file_path': msg[3],
            'timestamp': msg[4].strftime('%Y-%m-%d %H:%M:%S')
        }, room=request.sid)
    
    emit('message', {
        'username': 'System',
        'message': f"{username} has joined the chat",
        'type': 'text',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    username = data['username']
    message = data['message']
    message_type = data.get('type', 'text')
    file_path = data.get('file_path', None)
    
    # Store message in database
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO chat_messages 
        (room_id, sender_email, message, message_type, file_path)
        VALUES (%s, %s, %s, %s, %s)
    """, (room, username, message, message_type, file_path))
    
    mysql.connection.commit()
    cur.close()
    
    # Broadcast message to room
    emit('message', {
        'username': username,
        'message': message,
        'type': message_type,
        'file_path': file_path,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, room=room)

@socketio.on('typing')
def handle_typing(data):
    room = data['room']
    username = data['username']
    emit('typing', {'username': username}, room=room, include_self=False)

@app.route('/chat/upload', methods=['POST'])
def upload_chat_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'})
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
            
        # Generate unique filename
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
        file_path = os.path.join(CHAT_UPLOADS, filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'file_path': f'/chat_uploads/{filename}',
            'message': 'File uploaded successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Appointment Routes
@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    try:
        data = request.json
        cur = mysql.connection.cursor()
        
        # Check for conflicting appointments
        cur.execute("""
            SELECT COUNT(*) FROM book_appointment 
            WHERE doctor_name = %s 
            AND appointment_date = %s 
            AND appointment_time = %s 
            AND status != 'cancelled'
        """, (data['doctor'], data['date'], data['time']))
        
        if cur.fetchone()[0] > 0:
            return jsonify({
                'success': False,
                'message': 'This time slot is already booked'
            })
        
        # Generate video consultation link if needed
        consultation_link = None
        if data.get('is_video_consultation', False):
            consultation_link = f"https://meet.healthcare.com/{uuid.uuid4()}"
        
        # Insert appointment
        cur.execute("""
            INSERT INTO book_appointment 
            (user_email, doctor_name, specialization, appointment_date, 
             appointment_time, status, is_video_consultation, consultation_link, notes)
            VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s, %s)
        """, (
            data['email'],
            data['doctor'],
            data['specialization'],
            data['date'],
            data['time'],
            data.get('is_video_consultation', False),
            consultation_link,
            data.get('notes', '')
        ))
        
        mysql.connection.commit()
        appointment_id = cur.lastrowid
        cur.close()
        
        return jsonify({
            'success': True,
            'message': 'Appointment booked successfully',
            'appointment_id': appointment_id,
            'consultation_link': consultation_link
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    

    
    
@app.route('/get_prescriptions', methods=['GET'])
def get_prescriptions():
    try:
        user_email = request.args.get('email')
        if not user_email:
            return jsonify({'success': False, 'message': 'User email is required'})

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, appointment_id, doctor_email, prescription_text, dosage_instructions, duration, created_at
            FROM prescriptions
            WHERE user_email = %s
            ORDER BY created_at DESC
        """, (user_email,))
        
        rows = cur.fetchall()
        cur.close()
        
        prescriptions = []
        for row in rows:
            prescriptions.append({
                'id': row[0],
                'appointment_id': row[1],
                'doctor_email': row[2],
                'prescription_text': row[3],
                'dosage_instructions': row[4],
                'duration': row[5],
                'created_at': row[6].strftime('%Y-%m-%d') if row[6] else ''
            })
        
        return jsonify({'success': True, 'prescriptions': prescriptions})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})



@app.route('/get_appointments', methods=['GET'])
def get_appointments():
    try:
        email = request.args.get('email')
        is_doctor = request.args.get('is_doctor', 'false') == 'true'
        
        cur = mysql.connection.cursor()
        
        if is_doctor:
            cur.execute("""
                SELECT a.*, p.id as prescription_id, p.prescription_text,
                       f.followup_appointment_id, f.reason as followup_reason
                FROM book_appointment a
                LEFT JOIN prescriptions p ON a.id = p.appointment_id
                LEFT JOIN followup_appointments f ON a.id = f.original_appointment_id
                WHERE a.doctor_name = %s 
                ORDER BY a.appointment_date, a.appointment_time
            """, (email,))
        else:
            cur.execute("""
                SELECT a.*, p.id as prescription_id, p.prescription_text,
                       f.followup_appointment_id, f.reason as followup_reason
                FROM book_appointment a
                LEFT JOIN prescriptions p ON a.id = p.appointment_id
                LEFT JOIN followup_appointments f ON a.id = f.original_appointment_id
                WHERE a.user_email = %s 
                ORDER BY a.appointment_date, a.appointment_time
            """, (email,))
            
        appointments = cur.fetchall()
        cur.close()
        
        # Convert to list of dictionaries
        appointment_list = []
        for appt in appointments:
            appointment_list.append({
                'id': appt[0],
                'user_email': appt[1],
                'doctor_name': appt[2],
                'specialization': appt[3],
                'appointment_date': appt[4].strftime('%Y-%m-%d'),
                'appointment_time': appt[5],
                'status': appt[6],
                'is_video_consultation': bool(appt[7]),
                'consultation_link': appt[8],
                'notes': appt[9],
                'created_at': appt[10].strftime('%Y-%m-%d %H:%M:%S'),
                'prescription': {
                    'id': appt[11],
                    'text': appt[12]
                } if appt[11] else None,
                'followup': {
                    'appointment_id': appt[13],
                    'reason': appt[14]
                } if appt[13] else None
            })
            
        return jsonify({'success': True, 'appointments': appointment_list})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/update_appointment_status', methods=['POST'])
def update_appointment_status():
    try:
        data = request.json
        cur = mysql.connection.cursor()
        
        cur.execute("""
            UPDATE book_appointment 
            SET status = %s 
            WHERE id = %s
        """, (data['status'], data['id']))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': 'Status updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/add_prescription', methods=['POST'])
def add_prescription():
    try:
        data = request.json
        cur = mysql.connection.cursor()
        
        cur.execute("""
            INSERT INTO prescriptions 
            (appointment_id, user_email, doctor_email, prescription_text, 
             dosage_instructions, duration)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['appointment_id'],
            data['user_email'],
            data['doctor_email'],
            data['prescription_text'],
            data.get('dosage_instructions', ''),
            data.get('duration', '')
        ))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': 'Prescription added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/schedule_followup', methods=['POST'])
def schedule_followup():
    try:
        data = request.json
        cur = mysql.connection.cursor()
        
        # Book the follow-up appointment
        cur.execute("""
            INSERT INTO book_appointment 
            (user_email, doctor_name, specialization, appointment_date, 
             appointment_time, status, is_video_consultation, consultation_link, notes)
            VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s, %s)
        """, (
            data['user_email'],
            data['doctor_name'],
            data['specialization'],
            data['date'],
            data['time'],
            data.get('is_video_consultation', False),
            data.get('consultation_link'),
            'Follow-up appointment'
        ))
        
        followup_id = cur.lastrowid
        
        # Link it to the original appointment
        cur.execute("""
            INSERT INTO followup_appointments 
            (original_appointment_id, followup_appointment_id, reason)
            VALUES (%s, %s, %s)
        """, (
            data['original_appointment_id'],
            followup_id,
            data.get('reason', '')
        ))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            'success': True,
            'message': 'Follow-up appointment scheduled successfully',
            'followup_id': followup_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Medical Reports Routes
@app.route('/upload_report', methods=['POST'])
def upload_report():
    try:
        if 'reportFile' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
            
        file = request.files['reportFile']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'message': f'File type not allowed. Allowed types are: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Validate user email
        user_email = request.form.get('user_email')
        if not user_email:
            return jsonify({'success': False, 'message': 'User email is required'}), 400

        # Validate category
        category = request.form.get('category', 'other')
        valid_categories = ['Lab Tests', 'X-Rays', 'Prescriptions', 'Other']
        if category not in valid_categories:
            return jsonify({'success': False, 'message': 'Invalid category'}), 400
            
        # Save file with secure filename
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Save to database
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO uploadreport 
                (user_email, file_name, file_path, category, upload_date)
                VALUES (%s, %s, %s, %s, NOW())
            """, (user_email, file.filename, filename, category))
            
            mysql.connection.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Report uploaded successfully',
                'file_path': filename
            })
        except Exception as db_error:
            # If database insert fails, delete the uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise db_error
        finally:
            cur.close()
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error uploading report: {str(e)}'
        }), 500

@app.route('/get_reports', methods=['GET'])
def get_reports():
    try:
        email = request.args.get('email')
        category = request.args.get('category')
        
        cur = mysql.connection.cursor()
        
        if category:
            cur.execute("""
                SELECT * FROM uploadreport 
                WHERE user_email = %s AND category = %s
                ORDER BY upload_date DESC
            """, (email, category))
        else:
            cur.execute("""
                SELECT * FROM uploadreport 
                WHERE user_email = %s 
                ORDER BY upload_date DESC
            """, (email,))
            
        reports = cur.fetchall()
        cur.close()
        
        report_list = []
        for report in reports:
            report_list.append({
                'id': report[0],
                'user_email': report[1],
                'file_name': report[2],
                'file_path': report[3],
                'category': report[4],
                'upload_date': report[5].strftime('%Y-%m-%d %H:%M:%S'),
                'doctor_notes': report[6],
                'shared_with_doctors': json.loads(report[7]) if report[7] else []
            })
            
        return jsonify({
            'success': True, 
            'reports': report_list
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': str(e)
        }), 500

@app.route('/share_report', methods=['POST'])
def share_report():
    try:
        data = request.json
        cur = mysql.connection.cursor()
        
        # Get current shared doctors
        cur.execute("SELECT shared_with_doctors FROM uploadreport WHERE id = %s", (data['report_id'],))
        result = cur.fetchone()
        current_shared = json.loads(result[0]) if result[0] else []
        
        # Add new doctor if not already shared
        if data['doctor_email'] not in current_shared:
            current_shared.append(data['doctor_email'])
            
            cur.execute("""
                UPDATE uploadreport 
                SET shared_with_doctors = %s 
                WHERE id = %s
            """, (json.dumps(current_shared), data['report_id']))
            
            mysql.connection.commit()
        
        cur.close()
        return jsonify({'success': True, 'message': 'Report shared successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/add_report_note', methods=['POST'])
def add_report_note():
    try:
        data = request.json
        cur = mysql.connection.cursor()
        
        cur.execute("""
            UPDATE uploadreport 
            SET doctor_notes = %s 
            WHERE id = %s
        """, (data['note'], data['report_id']))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': 'Note added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_doctors', methods=['GET'])
def get_doctors():
    try:
        specialization = request.args.get('specialization')
        if not specialization:
            return jsonify({
                'success': False,
                'message': 'Specialization is required'
            }), 400

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT name, email 
            FROM doctor 
            WHERE specialization = %s
            AND is_approved = TRUE
        """, (specialization,))
        
        doctors = cur.fetchall()
        cur.close()

        doctor_list = [{
            'name': doctor[0],
            'email': doctor[1]
        } for doctor in doctors]

        return jsonify({
            'success': True,
            'doctors': doctor_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/get_available_slots', methods=['GET'])
def get_available_slots():
    try:
        doctor = request.args.get('doctor')
        date = request.args.get('date')

        if not all([doctor, date]):
            return jsonify({
                'success': False,
                'message': 'Doctor and date are required'
            }), 400

        # Define available time slots (9 AM to 5 PM, 1-hour intervals)
        all_slots = [f"{hour:02d}:00" for hour in range(9, 17)]
        
        # Get booked slots from database
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT appointment_time 
            FROM book_appointment 
            WHERE doctor_name = %s 
            AND appointment_date = %s
            AND status != 'cancelled'
        """, (doctor, date))
        
        booked_slots = [row[0] for row in cur.fetchall()]
        cur.close()

        # Format slots with availability
        slots = [{
            'time': slot,
            'booked': slot in booked_slots
        } for slot in all_slots]

        return jsonify({
            'success': True,
            'slots': slots
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5005)