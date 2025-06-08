from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import pickle
import re
import numpy as np
from datetime import datetime

# Load the model, scaler, and label encoder
with open('models/depression_model.pkl', 'rb') as file:
    model = pickle.load(file)

with open('scaler.pkl', 'rb') as file:
    scaler = pickle.load(file)
    
with open('label_encoder.pkl', 'rb') as file:
    label_encoder = pickle.load(file)

# Map depression levels to risk levels - using exact string matches from the model
risk_level_map = {
    'Minimal or No Depression': 'Minimal',
    'Mild Depression': 'Low',
    'Moderate Depression': 'Moderate',
    'Moderately Severe Depression': 'High',
    'Severe Depression': 'Very High'
}

# Define severity weights for different risk levels
severity_weights = {
    'Minimal': 1,
    'Low': 2,
    'Moderate': 3,
    'High': 4,
    'Very High': 5
}

# Define specialty weights based on severity
specialty_weights = {
    'Psychiatrist': {
        'Very High': 100,
        'High': 90,
        'Moderate': 80,
        'Low': 70,
        'Minimal': 60
    },
    'Clinical Psychologist': {
        'Very High': 90,
        'High': 85,
        'Moderate': 75,
        'Low': 65,
        'Minimal': 55
    },
    'Psychologist': {
        'Very High': 80,
        'High': 75,
        'Moderate': 70,
        'Low': 60,
        'Minimal': 50
    },
    'Therapist': {
        'Very High': 70,
        'High': 65,
        'Moderate': 60,
        'Low': 55,
        'Minimal': 45
    },
    'Counselor': {
        'Very High': 60,
        'High': 55,
        'Moderate': 50,
        'Low': 45,
        'Minimal': 40
    }
}

# Define location weights based on distance (assuming major cities as hubs)
location_weights = {
    'exact_match': 100,
    'nearby_city': 80,
    'major_city': 60,
    'other_city': 40
}

# Define location fallback mapping based on geographical proximity
location_fallback_map = {
    # Central Region
    'hetauda': ['Kathmandu', 'Bhaktapur', 'Lalitpur'],
    'bharatpur': ['Kathmandu', 'Bhaktapur', 'Pokhara'],
    'panauti': ['Bhaktapur', 'Kathmandu', 'Lalitpur'],
    'bidur': ['Kathmandu', 'Bhaktapur', 'Lalitpur'],
    'dharan': ['Biratnagar', 'Kathmandu'],
    'dhankuta': ['Biratnagar', 'Kathmandu'],
    'birgunj': ['Kathmandu', 'Bhaktapur'],
    'janakpur': ['Biratnagar', 'Kathmandu'],
    'gaur': ['Birgunj', 'Kathmandu'],
    'malangwa': ['Birgunj', 'Kathmandu'],
    'kalaiya': ['Birgunj', 'Kathmandu'],
    
    # Western Region
    'butwal': ['Pokhara', 'Kathmandu'],
    'bhairahawa': ['Butwal', 'Pokhara'],
    'tansen': ['Butwal', 'Pokhara'],
    'gorkha': ['Pokhara', 'Kathmandu'],
    'damauli': ['Pokhara', 'Kathmandu'],
    'syangja': ['Pokhara', 'Butwal'],
    'waling': ['Pokhara', 'Butwal'],
    
    # Eastern Region
    'ilam': ['Biratnagar', 'Kathmandu'],
    'damak': ['Biratnagar', 'Kathmandu'],
    'mechinagar': ['Biratnagar', 'Kathmandu'],
    'bhadrapur': ['Biratnagar', 'Kathmandu'],
    
    # Default fallback for unknown locations
    'default': ['Kathmandu', 'Pokhara', 'Biratnagar']
}

user_bp = Blueprint("user", __name__, "/")

# Database configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "insightify",
    "port": 3306
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
            conn = mysql.connector.connect(db_config)
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

        # Get all form fields
        fullname = data.get('fullname', '').strip()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        age = data.get('age')
        gender = data.get('gender', '').strip()
        location = data.get('location', '').strip()
        interest = data.get('interest', '').strip()

        # Required fields check
        required_fields = {
            'Full Name': fullname,
            'Email': email,
            'Password': password,
            'Age': age,
            'Gender': gender,
            'Location': location,
            'Area of Interest': interest
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            return jsonify({'success': False, 'message': f'Please fill in the following required fields: {", ".join(missing_fields)}'}), 400

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

        # Insert new user with all information
        hashed_pw = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (fullname, email, password, age, gender, location, interest) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (fullname, email, hashed_pw, age, gender, location, interest)
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
    print("-----1---")

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
        return redirect(url_for('user.login'))
    
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
    try:
        # Get the assessment type (self or others)
        assessment_type = request.form.get('assessment_type')
        
        # Get all question responses
        responses = []
        for key in request.form:
            if key.startswith('q'):
                responses.append(int(request.form[key]))
        
        if len(responses) != 9:  # Assuming there are 9 questions
            flash('Please answer all questions', 'error')
            return redirect(url_for('user.test'))

        # Calculate the total score
        score = sum(responses)
        
        # Store test results in session for processing
        session['score'] = score
        
        if assessment_type == 'self' and 'user_id' in session:
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor(dictionary=True)
                
                cursor.execute("""
                    SELECT fullname, age, gender, location, interest 
                    FROM users 
                    WHERE id = %s
                """, (session['user_id'],))
                
                user_info = cursor.fetchone()
                
                if user_info:
                    # Store user info in session
                    session['user_info'] = {
                        'fullname': user_info['fullname'],
                        'age': user_info['age'],
                        'gender': user_info['gender'],
                        'location': user_info['location'],
                        'interest': user_info['interest']
                    }
                    
                    # Scale the input using the loaded scaler
                    scaled_score = scaler.transform([[score]])
                    
                    # Make prediction using the model
                    prediction = model.predict(scaled_score)[0]
                    
                    # Convert prediction back to label
                    result = str(label_encoder.inverse_transform([prediction])[0])
                    
                    # Get risk level from mapping
                    risk_level = risk_level_map[result]
                    
                    # Store result in database
                    try:
                        cursor.execute(
                            'INSERT INTO results (user_id, total_score, result, risk_level, name, age, gender, location, interest) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                            (session['user_id'], score, result, risk_level, user_info['fullname'], user_info['age'], user_info['gender'], user_info['location'], user_info['interest'])
                        )
                        conn.commit()
                    except Exception as e:
                        print(f"Error storing result: {str(e)}")

                    # Store results in session
                    session['result'] = result
                    session['risk_level'] = risk_level
                    
                    # Redirect to result page
                    return redirect(url_for('user.result'))
                
            except Exception as e:
                print(f"Database error: {str(e)}")
                flash('A database error occurred', 'error')
                return redirect(url_for('user.test'))
            finally:
                if 'conn' in locals() and conn.is_connected():
                    cursor.close()
                    conn.close()
        
        # For 'others' assessment or if user info not found
        return redirect(url_for('user.phase2_questionnaire'))

    except Exception as e:
        print(f"Error in submit_test: {str(e)}")
        flash('An error occurred while processing your test', 'error')
        return redirect(url_for('user.test'))


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
    location = request.form['location'].lower()  # Convert to lowercase for matching
    interest = request.form['interest']

    # Store additional user info in session
    session['user_info'] = {
        'fullname': name,
        'age': age,
        'gender': gender,
        'location': location,
        'interest': interest
    }

    # Get score from session
    score = session.get('score')

    if score is None:
        return "Test score not found. Please retake the test.", 400

    try:
        # Scale the input using the loaded scaler
        scaled_score = scaler.transform([[score]])
        
        # Make prediction using the model
        prediction = model.predict(scaled_score)[0]
        
        # Convert prediction back to label
        result = str(label_encoder.inverse_transform([prediction])[0])
        
        # Get risk level from mapping
        risk_level = risk_level_map[result]
        
        # Store result in database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO results (user_id, total_score, result, risk_level, name, age, gender, location, interest) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (session['user_id'], score, result, risk_level, name, age, gender, location, interest)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # Store results in session
        session['result'] = result
        session['risk_level'] = risk_level
        
        # Redirect to result page
        return redirect(url_for('user.result'))
        
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        return f"Error processing results: {str(e)}", 500

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

@user_bp.route('/result')
def result():
    # Check if we have the required session data
    if 'score' not in session:
        return redirect(url_for('user.test'))
    
    # Get data from session
    score = session.get('score')
    user_info = session.get('user_info')
    result = session.get('result')
    risk_level = session.get('risk_level')
    
    if not all([score, user_info, result, risk_level]):
        return redirect(url_for('user.test'))
    
    # Get recommended doctors based on assessment and interest
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Get fallback locations for the user's location
        location = user_info['location'].lower()
        fallback_locations = location_fallback_map.get(location, location_fallback_map['default'])
        
        # Create the location condition for the SQL query
        location_conditions = ' OR '.join(['location = %s' for _ in fallback_locations])
        
        # Query to get all potential doctors
        query = f"""
            SELECT 
                name, specialty, location, experience, phone_number, area_of_interest,
                CASE 
                    WHEN location = %s THEN 'In your city'
                    ELSE CONCAT('Available in ', location)
                END as match_type,
                CASE
                    WHEN location = %s THEN 100
                    WHEN location IN ({', '.join(['%s' for _ in fallback_locations])}) THEN 80
                    ELSE 60
                END as match_score
            FROM doctors 
            WHERE location = %s OR location IN ({', '.join(['%s' for _ in fallback_locations])})
            ORDER BY match_score DESC
            LIMIT 10
        """
        
        # Create parameters list
        params = [
            location,  # For CASE WHEN location = %s
            location,  # For CASE WHEN location = %s
            *fallback_locations,  # For IN clause in match_score
            location,  # For WHERE location = %s
            *fallback_locations  # For WHERE location IN
        ]
        
        cursor.execute(query, params)
        doctors = cursor.fetchall()
        cursor.close()
        conn.close()

        # Format doctor information for display
        doctor_list = []
        for doc in doctors:
            match_percentage = round(doc['match_score'])
            doctor_info = f"{doc['name']} - {doc['specialty']}\n"
            doctor_info += f"Location: {doc['location']}\n"
            doctor_info += f"Experience: {doc['experience']} years\n"
            doctor_info += f"Area of Interest: {doc['area_of_interest']}\n"
            doctor_info += f"Contact: {doc['phone_number']}\n"
            doctor_info += f"Match Quality: {doc['match_type']} ({match_percentage}% match)"
            doctor_list.append(doctor_info)

    except Exception as e:
        print(f"Error fetching doctors: {str(e)}")
        doctor_list = []
    
    # Clear session data after retrieving it
    session.pop('score', None)
    session.pop('user_info', None)
    session.pop('result', None)
    session.pop('risk_level', None)
    
    return render_template('result.html',
                         score=score,
                         result=result,
                         risk_level=risk_level,
                         user_info=user_info,
                         doctors=doctor_list,
                         current_date=datetime.now().strftime('%B %d, %Y'))

# if __name__ == '__main__':
#     user_bp.run(debug=True, host='0.0.0.0', port=5000)
