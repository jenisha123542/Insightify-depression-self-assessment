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
        print("Connecting to database...")
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # First, let's check what columns exist in the users table
        cursor.execute("DESCRIBE users")
        user_columns = [row[0] for row in cursor.fetchall()]
        print("Available columns in users table:", user_columns)

        # First get total users (this should work regardless of columns)
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        print(f"Total users: {total_users}")

        # Get total tests
        cursor.execute("SELECT COUNT(*) FROM results")
        total_tests = cursor.fetchone()[0]
        print(f"Total tests: {total_tests}")

        # Get severe cases
        cursor.execute("SELECT COUNT(*) FROM results WHERE total_score > 20")
        severe_cases = cursor.fetchone()[0]
        print(f"Severe cases: {severe_cases}")

        # For monthly changes, we need to check what date column is available
        cursor.execute("DESCRIBE users")
        user_date_column = next((col[0] for col in cursor.fetchall() if 'date' in col[0].lower() or 'created' in col[0].lower()), 'date_registered')
        
        cursor.execute("DESCRIBE results")
        test_date_column = next((col[0] for col in cursor.fetchall() if 'date' in col[0].lower()), 'created_at')

        # Get monthly changes using the correct column names
        monthly_query = f"""
            SELECT 
                (SELECT COUNT(*) FROM users WHERE {user_date_column} >= DATE_SUB(NOW(), INTERVAL 1 MONTH)) as new_users,
                (SELECT COUNT(*) FROM results WHERE {test_date_column} >= DATE_SUB(NOW(), INTERVAL 1 MONTH)) as new_tests,
                (SELECT COUNT(*) FROM results WHERE total_score > 20 AND {test_date_column} >= DATE_SUB(NOW(), INTERVAL 1 MONTH)) as new_severe
        """
        print("Monthly query:", monthly_query)
        cursor.execute(monthly_query)
        monthly_stats = cursor.fetchone()
        print(f"Monthly changes: {monthly_stats}")

        stats = {
            'total_users': total_users,
            'total_tests': total_tests,
            'severe_cases': severe_cases,
            'monthly_changes': {
                'users': monthly_stats[0] if monthly_stats else 0,
                'tests': monthly_stats[1] if monthly_stats else 0,
                'severe': monthly_stats[2] if monthly_stats else 0
            }
        }

        print("Final stats:", stats)
        return jsonify({'success': True, 'stats': stats})

    except mysql.connector.Error as e:
        print(f"Database error in /get-stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Database error: {str(e)}',
            'stats': {
                'total_users': 0,
                'total_tests': 0,
                'severe_cases': 0,
                'monthly_changes': {'users': 0, 'tests': 0, 'severe': 0}
            }
        })
    except Exception as e:
        print(f"Unexpected error in /get-stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}',
            'stats': {
                'total_users': 0,
                'total_tests': 0,
                'severe_cases': 0,
                'monthly_changes': {'users': 0, 'tests': 0, 'severe': 0}
            }
        })
    finally:
        if cursor: 
            cursor.close()
        if connection: 
            connection.close()
        print("Database connection closed")

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

        # Delete the user safely
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        connection.commit()

        return jsonify({'success': True, 'message': 'User deleted successfully!'})

    except Exception as e:
        if connection:
            connection.rollback()
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

        # Start transaction
        cursor.execute("START TRANSACTION")

        # First verify the doctor exists
        cursor.execute("SELECT id FROM doctors WHERE id = %s", (doctor_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Doctor not found'}), 404

        # Delete the doctor
        cursor.execute("DELETE FROM doctors WHERE id = %s", (doctor_id,))

        # Reset auto-increment and reorder IDs
        cursor.execute("SET @counter = 0")
        cursor.execute("UPDATE doctors SET id = (@counter := @counter + 1)")
        cursor.execute("ALTER TABLE doctors AUTO_INCREMENT = 1")

        # Commit transaction
        connection.commit()
        return jsonify({'success': True, 'message': 'Doctor deleted successfully!'})

    except Exception as e:
        if connection:
            connection.rollback()
        print("Error deleting doctor:", e)
        return jsonify({'success': False, 'message': 'Failed to delete doctor'})
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


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

@admin_bp.route('/get-trend-data')
def get_trend_data():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Get all data grouped by month
        query = """
            SELECT 
                DATE_FORMAT(created_at, '%b %Y') as month,
                CASE 
                    WHEN total_score <= 4 THEN 'Minimal or No Depression'
                    WHEN total_score <= 9 THEN 'Mild Depression'
                    WHEN total_score <= 14 THEN 'Moderate Depression'
                    WHEN total_score <= 19 THEN 'Moderately Severe Depression'
                    ELSE 'Severe Depression'
                END as severity,
                COUNT(*) as count
            FROM results
            GROUP BY 
                DATE_FORMAT(created_at, '%b %Y'),
                CASE 
                    WHEN total_score <= 4 THEN 'Minimal or No Depression'
                    WHEN total_score <= 9 THEN 'Mild Depression'
                    WHEN total_score <= 14 THEN 'Moderate Depression'
                    WHEN total_score <= 19 THEN 'Moderately Severe Depression'
                    ELSE 'Severe Depression'
                END
            ORDER BY created_at ASC, severity ASC
        """
        cursor.execute(query)
        results = cursor.fetchall()

        # Process the results
        months = []
        data = {
            'Minimal or No Depression': [],
            'Mild Depression': [],
            'Moderate Depression': [],
            'Moderately Severe Depression': [],
            'Severe Depression': []
        }

        # Initialize data structure
        for row in results:
            month = row[0]  # Now in format 'MMM YYYY'
            if month not in months:
                months.append(month)
                # Add 0 for all categories in this month
                for category in data:
                    data[category].append(0)
            
            # Update the count for this category in this month
            month_index = months.index(month)
            severity = row[1]
            count = row[2]
            data[severity][month_index] = count

        # Format the response
        trends = {
            'labels': months,
            'minimal': data['Minimal or No Depression'],
            'mild': data['Mild Depression'],
            'moderate': data['Moderate Depression'],
            'moderately_severe': data['Moderately Severe Depression'],
            'severe': data['Severe Depression']
        }

        print("Generated trend data:", trends)  # Debug print

        return jsonify({
            'success': True,
            'trends': trends
        })

    except Exception as e:
        print(f"Error fetching trend data: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}',
            'trends': {
                'labels': [],
                'minimal': [],
                'mild': [],
                'moderate': [],
                'moderately_severe': [],
                'severe': []
            }
        })
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


