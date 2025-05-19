from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import cv2
import face_recognition
import numpy as np
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
from functools import wraps
import time
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/missing_persons'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')  # user or admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

class PersonPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo_path = db.Column(db.String(100), nullable=False)
    face_encoding = db.Column(db.LargeBinary)
    is_primary = db.Column(db.Boolean, default=False)
    missing_person_id = db.Column(db.Integer, db.ForeignKey('missing_person.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MissingPerson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(1), nullable=False)
    last_seen = db.Column(db.DateTime, nullable=False)
    last_seen_location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    contact_name = db.Column(db.String(100), nullable=False)
    contact_phone = db.Column(db.String(15), nullable=False)
    contact_email = db.Column(db.String(254), nullable=False)
    is_found = db.Column(db.Boolean, default=False)
    date_found = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    photos = db.relationship('PersonPhoto', backref='person', lazy=True)

    @property
    def primary_photo(self):
        return next((photo for photo in self.photos if photo.is_primary), self.photos[0] if self.photos else None)

class MatchReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    photo_path = db.Column(db.String(100), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_notes = db.Column(db.Text)
    missing_person_id = db.Column(db.Integer, db.ForeignKey('missing_person.id'), nullable=False)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Add this new route at the beginning of your routes
@app.route('/')
def landing():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('landing.html')

# Update the login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('Welcome back! You have been logged in successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html')

# Update the register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('register'))
            
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different email or login.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password, name=name)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login to continue.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Error during registration. Please try again.', 'danger')
    
    return render_template('register.html')

# Update the logout route
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('landing'))

# Update the index route to require login
@app.route('/dashboard')
@login_required
def index():
    # Get filter parameters
    age_range = request.args.get('age', '')
    gender = request.args.get('gender', '')
    location = request.args.get('location', '')
    date = request.args.get('date', '')

    # Start with base query
    query = MissingPerson.query.filter_by(is_found=False)

    # Apply filters
    if age_range:
        if age_range == '0-18':
            query = query.filter(MissingPerson.age <= 18)
        elif age_range == '19-30':
            query = query.filter(MissingPerson.age.between(19, 30))
        elif age_range == '31-50':
            query = query.filter(MissingPerson.age.between(31, 50))
        elif age_range == '51+':
            query = query.filter(MissingPerson.age >= 51)

    if gender:
        query = query.filter_by(gender=gender)

    if location:
        query = query.filter(MissingPerson.last_seen_location.ilike(f'%{location}%'))

    if date:
        query = query.filter(MissingPerson.last_seen == datetime.strptime(date, '%Y-%m-%d'))

    # Get filtered results
    missing_persons = query.all()
    
    # Get found persons count
    found_persons = MissingPerson.query.filter_by(is_found=True).all()
    
    # Get active cases (missing persons not found)
    active_cases = MissingPerson.query.filter_by(is_found=False).all()
    
    # Get AI matches count (you can implement this based on your needs)
    ai_matches = []

    return render_template('index.html', 
                         missing_persons=missing_persons, 
                         found_persons=found_persons,
                         active_cases=active_cases,
                         ai_matches=ai_matches)

@app.route('/register_person', methods=['GET', 'POST'])
@login_required
def register_person():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            age = int(request.form['age'])
            gender = request.form['gender']
            last_seen = datetime.strptime(request.form['last_seen'], '%Y-%m-%dT%H:%M')
            last_seen_location = request.form['last_seen_location']
            description = request.form['description']
            contact_name = request.form['contact_name']
            contact_phone = request.form['contact_phone']
            contact_email = request.form['contact_email']
            
            # Get photo data
            photo_data = request.form['photo_data']
            photos = json.loads(photo_data)  # Parse the JSON string of photos
            
            # Create new missing person record
            missing_person = MissingPerson(
                name=name,
                age=age,
                gender=gender,
                last_seen=last_seen,
                last_seen_location=last_seen_location,
                description=description,
                contact_name=contact_name,
                contact_phone=contact_phone,
                contact_email=contact_email,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(missing_person)
            db.session.flush()  # Get the ID without committing
            
            # Process each photo
            for i, photo_data in enumerate(photos):
                # Save photo
                photo_filename = f"person_{missing_person.id}_{i}_{int(time.time())}.jpg"
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                
                # Convert base64 to image and save
                photo_data = photo_data.split(',')[1]
                photo_bytes = base64.b64decode(photo_data)
                with open(photo_path, 'wb') as f:
                    f.write(photo_bytes)
                
                # Process face encoding
                face_encoding = process_face_encoding(photo_path)
                if face_encoding is not None:
                    # Create photo record
                    person_photo = PersonPhoto(
                        photo_path=photo_filename,
                        face_encoding=face_encoding,
                        is_primary=(i == 0),  # First photo is primary
                        missing_person_id=missing_person.id
                    )
                    db.session.add(person_photo)
            
            db.session.commit()
            flash('Missing person registered successfully!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error registering missing person: {str(e)}', 'error')
            return redirect(url_for('register_person'))
    
    return render_template('register_person.html')

@app.route('/missing_person/<int:id>')
def missing_person_detail(id):
    person = MissingPerson.query.get_or_404(id)
    return render_template('missing_person_detail.html', person=person)

@app.route('/match', methods=['GET', 'POST'])
@login_required
def match_person():
    if request.method == 'POST':
        try:
            # Get base64 image data
            photo_data = request.form.get('photo')
            if not photo_data:
                flash('No photo captured', 'error')
                return redirect(url_for('match_person'))
            
            # Convert base64 to image file
            photo_data = photo_data.split(',')[1]
            image_data = base64.b64decode(photo_data)
            image = Image.open(BytesIO(image_data))
            
            # Save the image
            filename = f"match_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(photo_path)

            # Process uploaded image with optimized parameters
            unknown_image = face_recognition.load_image_file(photo_path)
            
            # Use CNN face detection for better accuracy
            face_locations = face_recognition.face_locations(unknown_image, model="cnn")
            
            if not face_locations:
                os.remove(photo_path)
                flash('No face detected in the captured photo. Please try again with a clearer photo.', 'error')
                return redirect(url_for('match_person'))

            # Get face encodings with optimized parameters
            unknown_encodings = face_recognition.face_encodings(
                unknown_image,
                face_locations,
                num_jitters=10,  # Increased jitters for better accuracy
                model="large"    # Using large model for better accuracy
            )
            
            if not unknown_encodings:
                os.remove(photo_path)
                flash('Could not process face features. Please try again with a clearer photo.', 'error')
                return redirect(url_for('match_person'))
            
            # Get all missing persons
            missing_persons = MissingPerson.query.filter_by(is_found=False).all()
            matches = []
            
            # Process each person's photos
            for person in missing_persons:
                if not person.photos:
                    continue

                best_match = None
                best_confidence = 0

                # Compare with each photo of the person
                for photo in person.photos:
                    if not photo.face_encoding:
                        continue

                    known_encoding = np.frombuffer(photo.face_encoding, dtype=np.float64)
                    
                    # Compare with all detected faces
                    for unknown_encoding in unknown_encodings:
                        # Calculate face distance
                        distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
                        base_confidence = (1 - distance) * 100

                        # Enhanced quality checks
                        if base_confidence > 70:  # Lower initial threshold to catch more potential matches
                            # Calculate face size ratio
                            face_height = face_locations[0][2] - face_locations[0][0]
                            face_width = face_locations[0][1] - face_locations[0][3]
                            face_size_ratio = (face_height * face_width) / (unknown_image.shape[0] * unknown_image.shape[1])
                            
                            # Enhanced size boost calculation
                            size_confidence_boost = min(face_size_ratio * 400, 25)  # Increased multiplier and max boost
                            
                            # Calculate facial features quality
                            face_landmarks = face_recognition.face_landmarks(unknown_image, face_locations)
                            landmarks_quality = 1.0
                            if face_landmarks:
                                # Check for all major facial features
                                required_landmarks = [
                                    'left_eye', 'right_eye', 'nose_bridge', 'nose_tip',
                                    'top_lip', 'bottom_lip', 'left_eyebrow', 'right_eyebrow',
                                    'chin'
                                ]
                                detected_landmarks = sum(1 for landmark in required_landmarks if landmark in face_landmarks[0])
                                landmarks_quality = detected_landmarks / len(required_landmarks)
                            
                            # Calculate face angle quality
                            face_angle_quality = 1.0
                            if face_landmarks and 'left_eye' in face_landmarks[0] and 'right_eye' in face_landmarks[0]:
                                left_eye = face_landmarks[0]['left_eye']
                                right_eye = face_landmarks[0]['right_eye']
                                left_eye_center = np.mean(left_eye, axis=0)
                                right_eye_center = np.mean(right_eye, axis=0)
                                eye_angle = np.abs(np.arctan2(right_eye_center[1] - left_eye_center[1],
                                                            right_eye_center[0] - left_eye_center[0]))
                                face_angle_quality = 1.0 - min(eye_angle / (np.pi/4), 0.5)
                            
                            # Calculate final confidence with enhanced factors
                            final_confidence = base_confidence + size_confidence_boost
                            final_confidence *= (0.85 + 0.15 * landmarks_quality)  # Increased base quality factor
                            final_confidence *= (0.85 + 0.15 * face_angle_quality)  # Increased base quality factor
                            
                            # Additional boost for high-quality matches
                            if base_confidence > 85:
                                final_confidence *= 1.2  # Increased boost for high-quality matches
                            
                            # Additional boost for perfect landmarks
                            if landmarks_quality > 0.9:
                                final_confidence *= 1.1  # 10% boost for nearly perfect landmarks

                            if final_confidence > best_confidence:
                                best_confidence = final_confidence
                                best_match = {
                                    'person': person,
                                    'confidence': final_confidence,
                                    'quality_metrics': {
                                        'base_confidence': base_confidence,
                                        'size_boost': size_confidence_boost,
                                        'landmarks_quality': landmarks_quality * 100,
                                        'face_angle_quality': face_angle_quality * 100
                                    }
                                }

                # Higher threshold for matches (85%)
                if best_match and best_confidence > 85:
                    matches.append(best_match)
            
            # Clean up temporary file
            os.remove(photo_path)
            
            if matches:
                # Sort matches by confidence
                matches.sort(key=lambda x: x['confidence'], reverse=True)
                return render_template('match_result.html', matches=matches)
            else:
                flash('No matches found. Please try again with a clearer photo.', 'info')
                return redirect(url_for('match_person'))
                
        except Exception as e:
            print(f"Error during face recognition: {str(e)}")
            flash(f'Error during face recognition: {str(e)}', 'error')
            return redirect(url_for('match_person'))
    
    return render_template('match.html')

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    if query:
        # Search in name, description, and location
        results = MissingPerson.query.filter(
            (MissingPerson.name.ilike(f'%{query}%')) |
            (MissingPerson.description.ilike(f'%{query}%')) |
            (MissingPerson.last_seen_location.ilike(f'%{query}%'))
        ).all()
    else:
        results = []
    return render_template('search_results.html', results=results, query=query)

@app.route('/found')
@login_required
def found_persons():
    # Get filter parameters
    age_range = request.args.get('age', '')
    gender = request.args.get('gender', '')
    location = request.args.get('location', '')
    date = request.args.get('date', '')

    # Start with base query
    query = MissingPerson.query.filter_by(is_found=True)

    # Apply filters
    if age_range:
        if age_range == '0-18':
            query = query.filter(MissingPerson.age <= 18)
        elif age_range == '19-30':
            query = query.filter(MissingPerson.age.between(19, 30))
        elif age_range == '31-50':
            query = query.filter(MissingPerson.age.between(31, 50))
        elif age_range == '51+':
            query = query.filter(MissingPerson.age >= 51)

    if gender:
        query = query.filter_by(gender=gender)

    if location:
        query = query.filter(MissingPerson.last_seen_location.ilike(f'%{location}%'))

    if date:
        query = query.filter(MissingPerson.last_seen == datetime.strptime(date, '%Y-%m-%d'))

    # Get filtered results
    found_persons = query.all()

    return render_template('found_persons.html', found_persons=found_persons)

@app.route('/missing')
@login_required
def missing_persons():
    # Get filter parameters
    age_range = request.args.get('age', '')
    gender = request.args.get('gender', '')
    location = request.args.get('location', '')
    date = request.args.get('date', '')

    # Start with base query
    query = MissingPerson.query.filter_by(is_found=False)

    # Apply filters
    if age_range:
        if age_range == '0-18':
            query = query.filter(MissingPerson.age <= 18)
        elif age_range == '19-30':
            query = query.filter(MissingPerson.age.between(19, 30))
        elif age_range == '31-50':
            query = query.filter(MissingPerson.age.between(31, 50))
        elif age_range == '51+':
            query = query.filter(MissingPerson.age >= 51)

    if gender:
        query = query.filter_by(gender=gender)

    if location:
        query = query.filter(MissingPerson.last_seen_location.ilike(f'%{location}%'))

    if date:
        query = query.filter(MissingPerson.last_seen == datetime.strptime(date, '%Y-%m-%d'))

    # Get filtered results
    missing_persons = query.all()

    return render_template('missing_persons.html', missing_persons=missing_persons)

@app.route('/missing_person/<int:id>/mark_found', methods=['POST'])
@login_required
def mark_person_found(id):
    try:
        person = MissingPerson.query.get_or_404(id)
        person.is_found = True
        person.date_found = datetime.now()
        db.session.commit()
        flash('Person has been marked as found', 'success')
    except Exception as e:
        flash(f'Error marking person as found: {str(e)}', 'error')
    return redirect(url_for('missing_person_detail', id=id))

@app.route('/missing_person/<int:id>/mark_missing', methods=['POST'])
@login_required
def mark_person_missing(id):
    try:
        person = MissingPerson.query.get_or_404(id)
        person.is_found = False
        person.date_found = None
        db.session.commit()
        flash('Person has been marked as missing again', 'info')
    except Exception as e:
        flash(f'Error marking person as missing: {str(e)}', 'error')
    return redirect(url_for('missing_person_detail', id=id))

def process_face_encoding(image_path):
    try:
        # Load the image file
        image = face_recognition.load_image_file(image_path)
        
        # Find all face locations in the image with more accurate model
        face_locations = face_recognition.face_locations(image, model="cnn")
        
        if not face_locations:
            print(f"No face detected in {image_path}")
            return None
            
        # Get face encodings with more jitters for better accuracy
        face_encodings = face_recognition.face_encodings(
            image, 
            face_locations,
            num_jitters=10,  # Increased from 1 to 10 for better accuracy
            model="large"    # Using large model for better accuracy
        )
        
        if not face_encodings:
            print(f"Could not encode face in {image_path}")
            return None
            
        # Return the first face encoding (assuming one face per photo)
        return face_encodings[0].tobytes()
        
    except Exception as e:
        print(f"Error processing face encoding: {str(e)}")
        return None

@app.route('/find_person', methods=['GET', 'POST'])
def find_person():
    if request.method == 'POST':
        if 'photo' not in request.files:
            flash('No photo uploaded', 'error')
            return redirect(request.url)
            
        photo = request.files['photo']
        if photo.filename == '':
            flash('No photo selected', 'error')
            return redirect(request.url)
            
        if photo:
            try:
                # Save the uploaded photo temporarily
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_upload.jpg')
                photo.save(temp_path)
                
                # Process the uploaded photo
                uploaded_encoding = process_face_encoding(temp_path)
                
                if uploaded_encoding is None:
                    flash('No face detected in the uploaded photo. Please try again with a clearer photo.', 'error')
                    os.remove(temp_path)
                    return redirect(request.url)
                
                # Convert bytes back to numpy array
                uploaded_encoding = np.frombuffer(uploaded_encoding, dtype=np.float64)
                
                # Get all missing persons
                missing_persons = MissingPerson.query.filter_by(is_found=False).all()
                matches = []
                
                for person in missing_persons:
                    for photo in person.photos:
                        if photo.face_encoding:
                            # Convert stored encoding to numpy array
                            stored_encoding = np.frombuffer(photo.face_encoding, dtype=np.float64)
                            
                            # Compare faces with a more lenient tolerance
                            face_distance = face_recognition.face_distance([stored_encoding], uploaded_encoding)[0]
                            
                            # Lower threshold for matching (0.6 is more lenient than default 0.6)
                            if face_distance < 0.6:
                                matches.append(person)
                                break  # Break after first match for this person
                
                # Clean up temporary file
                os.remove(temp_path)
                
                if matches:
                    return render_template('find_person.html', matches=matches)
                else:
                    flash('No matches found. Please try again with a different angle or better lighting.', 'error')
                    return redirect(request.url)
                    
            except Exception as e:
                print(f"Error in find_person: {str(e)}")
                flash('An error occurred while processing the photo. Please try again.', 'error')
                return redirect(request.url)
                
    return render_template('find_person.html')

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {str(e)}")
    app.run(debug=True) 