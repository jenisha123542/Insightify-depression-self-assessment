from flask import Blueprint, current_app, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

admin_bp = Blueprint("admin",__name__, template_folder='templates', static_folder='static')
# current_app.secret_key = 'your-secret-key-123'  # Change this to a strong secret key in production

# Database configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "insightify"
}
 
def get_unread_count():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS count FROM messages WHERE reply IS NULL OR reply = ''")
        result = cursor.fetchone()
        return result['count'] if result else 0
    except:
        return 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@admin_bp.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(current_app.static_folder, filename)

@admin_bp.route('/')
def index():
    return render_template('index.html')

@admin_bp.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        return render_template('admin_login.html')
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data received'}), 400
        
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')

    print(f"Attempting login for email: {email}")  # Debug
    print(f"Password received: {password}")  # Debug

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, fullname, email, password FROM admins WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        print(f"User from DB: {user}")  # Debug
        
        if user:
            print(f"Stored hashed password: {user['password']}")  # Debug
            print(f"Password match result: {check_password_hash(user['password'], password)}")  # Debug
        
        if user and check_password_hash(user['password'], password):
            session["admin_id"]=user["id"]
            return jsonify({
                'success': True,
                'message': 'Login successful!',
                'user': {
                    'id': user['id'],
                    'fullname': user['fullname'],
                    'email': user['email']
                }
            }), 200
        return jsonify({'success': False, 'message': 'Invalid credentials!'}), 401
    except Exception as e:
        print(f"Error during login: {e}")  # Debug
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


@admin_bp.route('/admin_dashboard')
def admin_dashboard():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS count FROM messages WHERE reply IS NULL OR reply = ''")
        result = cursor.fetchone()
        unread_count = result['count'] if result else 0
        return render_template("admin_dashboard.html", unread_count=unread_count)
    except Exception as e:
        print("Error fetching dashboard data:", e)
        return render_template("admin_dashboard.html", unread_count=0)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/get-stats')
def get_stats():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        print("Total users from DB:", total_users)  # Debug print

        stats = {
            'total_users': total_users
        }

        return jsonify({'success': True, 'stats': stats})

    except Exception as e:
        print("Error in /get-stats:", e)
        return jsonify({'success': False, 'message': str(e)})

    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@admin_bp.route('/users')
def view_users():
    try:
        # Connect to the database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # Query to get all users from the 'users' table
        cursor.execute("SELECT id, fullname, email, date_registered FROM users")
        users = cursor.fetchall()
        unread_count = get_unread_count()
        # Render the 'users.html' template with the list of users
        return render_template('users.html', users=users, unread_count=unread_count)

    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({'success': False, 'message': 'Error fetching users.'})

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@admin_bp.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Query to delete the user by id
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        connection.commit()

        return jsonify({'success': True, 'message': 'User deleted successfully!'})

    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'success': False, 'message': 'Error deleting user.'})

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@admin_bp.route('/admin-logout', methods=['GET'])
def admin_logout():
    session.pop('admin_id', None)  # Remove the admin ID from the session
    return jsonify({'success': True, 'redirect': '/admin/admin_login'})  # Redirect to login page

@admin_bp.route('/doctors')
def view_doctors():
    try:
        # Connect to the database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # Query to get all doctors from the 'doctors' table with all fields
        cursor.execute("""
            SELECT id, name, specialty, location, experience, 
                   phone_number, area_of_interest 
            FROM doctors
        """)
        doctors = cursor.fetchall()
        unread_count = get_unread_count()
        return render_template('doctors.html', doctors=doctors, unread_count=unread_count)

    except Exception as e:
        print(f"Error fetching doctors: {e}")
        return jsonify({'success': False, 'message': 'Error fetching doctors.'})

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@admin_bp.route('/add-doctor', methods=['POST'])
def add_doctor():
    try:
        data = request.get_json()
        name = data.get('name')
        specialty = data.get('specialty')
        location = data.get('location')
        experience = data.get('experience')
        phone_number = data.get('phone_number')
        area_of_interest = data.get('area_of_interest')

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        cursor.execute(
            """INSERT INTO doctors (name, specialty, location, 
                                  experience, phone_number, area_of_interest) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (name, specialty, location, experience, phone_number, area_of_interest)
        )
        connection.commit()

        return jsonify({'success': True, 'message': 'Doctor added successfully!'})
    except Exception as e:
        print("Error adding doctor:", e)
        return jsonify({'success': False, 'message': 'Failed to add doctor'})
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@admin_bp.route('/delete-doctor/<int:doctor_id>', methods=['DELETE'])
def delete_doctor(doctor_id):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # First verify the doctor exists
        cursor.execute("SELECT id FROM doctors WHERE id = %s", (doctor_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Doctor not found'}), 404

        cursor.execute("DELETE FROM doctors WHERE id = %s", (doctor_id,))
        connection.commit()

        return jsonify({'success': True, 'message': 'Doctor deleted successfully!'})
    except Exception as e:
        print("Error deleting doctor:", e)
        return jsonify({'success': False, 'message': 'Failed to delete doctor'})
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@admin_bp.route('/messages', methods=['GET', 'POST'], endpoint='admin_contact')
def messages():
    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Query to fetch all messages
        cursor.execute("SELECT * FROM messages")  # Adjust table name if necessary
        messages = cursor.fetchall()
        unread_count = get_unread_count()
        return render_template('messages.html', messages=messages, unread_count=unread_count)
        
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return "Error fetching messages from the database", 500
    finally:
        if conn:
            conn.close()        

    

from datetime import datetime

@admin_bp.route('/reply-message/<int:message_id>', methods=['POST'])
def reply_message(message_id):
    data = request.get_json()
    reply = data.get('reply', '')

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        query = "UPDATE messages SET reply = %s, replied_at = %s WHERE id = %s"
        cursor.execute(query, (reply, datetime.now(), message_id))
        conn.commit()

        return jsonify({'success': True, 'message': 'Reply saved successfully.'})

    except Exception as e:
        print("Reply Error:", e)
        return jsonify({'success': False, 'message': 'Failed to save reply.'})

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/delete-message/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        cursor.execute("DELETE FROM messages WHERE id = %s", (message_id,))
        connection.commit()

        return jsonify({'success': True, 'message': 'Message deleted successfully!'})
    except Exception as e:
        print("Error deleting message:", e)
        return jsonify({'success': False, 'message': 'Failed to delete message'})
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@admin_bp.route('/resultsmgmt')
def resultsmgmt():
    try:
        # Connect to the database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # Get unread messages count
        unread_count = get_unread_count()
        
        # Get test results data (you can modify this query based on your needs)
        cursor.execute("SELECT * FROM results")
        results = cursor.fetchall()
        
        return render_template('resultsmgmt.html', results=results, unread_count=unread_count)
    
    except Exception as e:
        print(f"Error fetching results: {e}")
        return render_template('resultsmgmt.html', results=[], unread_count=0)
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


