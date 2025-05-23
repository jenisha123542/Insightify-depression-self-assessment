from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import pickle
import re
import numpy as np

# Load the model
with open('models/depression_model.pkl', 'rb') as file:
    model = pickle.load(file)

# Load the scaler too
scaler = pickle.load(open('scaler.pkl', 'rb'))    

user_bp = Blueprint("user", __name__, "/")

# Database configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "insightify"
}

# Static routes
@user_bp.route('/')
def index():
    return render_template('index.html')

@user_bp.route('/learn-about-depression')
def depression():
    return render_template('depression.html')

@user_bp.route('/about')
def about():
    return render_template('about.html')

@user_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO messages (name, email, content)
                VALUES (%s, %s, %s)
            """, (name, email, message))

            conn.commit()

            # Flash success message and redirect to the same contact page
            flash("Your message has been sent successfully!", "success")
            return redirect(url_for('user.contact'))

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            flash("Error saving your message. Please try again.", "error")
            return redirect(url_for('user.contact'))
        finally:
            if conn:
                conn.close()

    return render_template('contact.html')

@user_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@user_bp.route('/terms')
def terms():
    return render_template('terms.html')

# Authentication routes
@user_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400

        fullname = data.get('fullname', '').strip()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')

        # Field presence check
        if not all([fullname, email, password]):
            return jsonify({'success': False, 'message': 'All fields are required!'}), 400

        # Email format check
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            return jsonify({'success': False, 'message': 'Invalid email format!'}), 400

        # Password strength validation
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,}$'
        if not re.match(password_regex, password):
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.'
            }), 400

        # Connect to DB
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Email already exists!'}), 400

        # Insert new user
        hashed_pw = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (fullname, email, password) VALUES (%s, %s, %s)",
            (fullname, email, hashed_pw)
        )
        conn.commit()

        return jsonify({'success': True, 'message': 'Signup successful!'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


from flask import session  # Make sure this is imported

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data received'}), 400
        
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'message': 'All fields required!'}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, fullname, email, password FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            # ✅ Set session after successful login
            session['user_id'] = user['id']
            session['fullname'] = user['fullname']
            session['email'] = user['email']

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
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


@user_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()  # clear all session data
    return redirect(url_for('user.index'))

@user_bp.route('/contact', methods=['GET', 'POST'], endpoint='user_contact')
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Now, insert this data into the MySQL database
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO messages (name, email, content)
                VALUES (%s, %s, %s)
            """, (name, email, message))

            conn.commit()
            
            return redirect(url_for('user.contact'))  # Correct the redirect URL
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return "Error saving your message", 500
        finally:
            if conn:
                conn.close()
    return render_template('contact.html')

@user_bp.route('/test')
def test():
    if 'user_id' not in session:
        return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
            </head>
            <body>
                <script>
                    // Wait until SweetAlert2 is loaded
                    window.onload = function() {
                        Swal.fire({
                            icon: 'warning',
                            title: 'Hold on!',
                            text: 'You need to login to take the test.',
                            confirmButtonText: 'Login Now',
                            confirmButtonColor: '#0f2852'
                        }).then(() => {
                            window.location.href = "{{ url_for('user.login') }}";
                        });
                    }
                </script>
            </body>
            </html>
        ''')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Get all questions
        cursor.execute("SELECT * FROM questions")
        questions = cursor.fetchall()

        # Get all options
        question_ids = [q['id'] for q in questions]
        format_strings = ','.join(['%s'] * len(question_ids))
        cursor.execute(f"SELECT * FROM options WHERE question_id IN ({format_strings})", tuple(question_ids))
        options = cursor.fetchall()

        # Group options by question_id
        from collections import defaultdict
        options_dict = defaultdict(list)
        for opt in options:
            options_dict[opt['question_id']].append(opt)

        return render_template('test.html', questions=questions, options=options_dict)

    except Exception as e:
        return f"Error loading test: {str(e)}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@user_bp.route('/submit_test', methods=['POST'])
def submit_test():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    user_id = session['user_id']

    # Collect answers and calculate total_score
    answers = []
    total_score = 0
    for i in range(1, 10):
        selected_option = request.form.get(f'q{i}')
        if selected_option:
            score = int(selected_option)
            answers.append(score)
            total_score += score

    # ✅ Store score in session
    session['total_score'] = total_score

    # Proceed to phase 2
    return redirect(url_for('user.phase2_questionnaire'))


@user_bp.route('/phase2', methods=['GET'])
def phase2_questionnaire():
    return render_template('phase2.html') 

@user_bp.route('/submit_questionnaire', methods=['POST'])
def submit_questionnaire():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    name = request.form['name']
    age = request.form['age']
    gender = request.form['gender']
    location = request.form['location']
    interest = request.form['interest']

    # Store additional user info in session (optional)
    session['user_info'] = {
        'name': name,
        'age': age,
        'gender': gender,
        'location': location,
        'interest': interest
    }

    # ✅ Get score from session
    total_score = session.get('total_score')

    if total_score is None:
        return "Test score not found. Please retake the test.", 400
    
    # Scale the score properly before prediction
    import pandas as pd
    score_df = pd.DataFrame([[total_score]], columns=['PHQ-9 Total Score'])
    scaled_score = scaler.transform(score_df)

    # ✅ Predict using model
    prediction = model.predict(scaled_score)[0]
    print("Raw model prediction:", prediction)
    print("Model prediction output:", prediction)

    # ✅ Map prediction
    prediction_map = {
    "Minimal": ("Minimal or No Depression", "Low"),
    "Mild": ("Mild Depression", "Moderate"),
    "Moderate": ("Moderate Depression", "Moderate"),
    "Moderately": ("Moderately Severe Depression", "High"),
    "Severe": ("Severe Depression", "Very High")
    }

    print("Total score (raw):", total_score)
    print("Scaled score:", scaled_score) 
    result, risk_level = prediction_map.get(prediction, ("Unknown", "Unknown"))
    if result == "Unknown":
        print(f"Warning: Unknown prediction '{prediction}'")
    

    # ✅ Store result in database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    print("Params for insert:", (session['user_id'], total_score, result, risk_level, name, age, gender, location, interest))
    cursor.execute(
    'INSERT INTO results (user_id, total_score, result, risk_level, name, age, gender, location, interest) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
    (session['user_id'], total_score, result, risk_level, name, age, gender, location, interest)
)
    conn.commit()
    cursor.close()
    conn.close()

    # ✅ Render result page
    return render_template('result.html', score=total_score, result=result, risk_level=risk_level)

# This route is for the prediction part (machine learning model)
@user_bp.route('/predict', methods=['POST'])
def predict_depression():
    try:
        data = request.get_json()
        total_score = data.get('total_score')

        if total_score is None:
            return jsonify({'error': 'Total score not provided'}), 400

        prediction = model.predict([[total_score]])  # model is already loaded
        result = prediction[0]

        return jsonify({'prediction': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# if __name__ == '__main__':
#     user_bp.run(debug=True, host='0.0.0.0', port=5000)
