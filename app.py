from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import cv2
import face_recognition
import numpy as np
from datetime import datetime, timedelta
import base64
from io import BytesIO
from PIL import Image
from functools import wraps
import time
import json
from flask_mail import Mail, Message
from twilio.rest import Client

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-for-development')
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}/{os.getenv('DB_NAME', 'missing_persons')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Email Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_MAX_EMAILS'] = 100
app.config['MAIL_ASCII_ATTACHMENTS'] = False
app.config['MAIL_SUPPRESS_SEND'] = False

# Twilio Configuration
app.config['TWILIO_ACCOUNT_SID'] = os.getenv('TWILIO_ACCOUNT_SID')
app.config['TWILIO_AUTH_TOKEN'] = os.getenv('TWILIO_AUTH_TOKEN')
app.config['TWILIO_WHATSAPP_NUMBER'] = os.getenv('TWILIO_WHATSAPP_NUMBER')

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
mail = Mail(app)
db = SQLAlchemy(app)

# Initialize Twilio client only if credentials are available
twilio_client = None
if app.config['TWILIO_ACCOUNT_SID'] and app.config['TWILIO_AUTH_TOKEN']:
    twilio_client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Add this new route at the beginning of your routes
@app.route('/')
def landing():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

# Update the login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
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
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html')

# Update the register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
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
def dashboard():
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
            return redirect(url_for('dashboard'))
            
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
            
            # Use HOG model for faster face detection
            face_locations = face_recognition.face_locations(unknown_image, model="hog")
            
            if not face_locations:
                os.remove(photo_path)
                flash('No face detected in the captured photo. Please try again with a clearer photo.', 'error')
                return redirect(url_for('match_person'))

            # Get face encodings with optimized parameters
            unknown_encodings = face_recognition.face_encodings(
                unknown_image,
                face_locations,
                num_jitters=1,  # Reduced jitters for speed
                model="small"   # Using small model for speed
            )
            
            if not unknown_encodings:
                os.remove(photo_path)
                flash('Could not process face features. Please try again with a clearer photo.', 'error')
                return redirect(url_for('match_person'))
            
            # Get all missing persons with their photos preloaded
            missing_persons = MissingPerson.query.filter_by(is_found=False).options(
                db.joinedload(MissingPerson.photos)
            ).all()
            
            matches = []
            auto_found_person = None
            
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
                        
                        # Quick initial check with higher threshold
                        if distance < 0.6:  # More lenient threshold for initial check
                            # Simplified confidence calculation for speed
                            base_confidence = (1 - distance) * 100
                            
                            # Calculate face size ratio (simplified)
                            face_height = face_locations[0][2] - face_locations[0][0]
                            face_width = face_locations[0][1] - face_locations[0][3]
                            face_size_ratio = (face_height * face_width) / (unknown_image.shape[0] * unknown_image.shape[1])
                            size_confidence_boost = min(face_size_ratio * 300, 20)
                            
                            # Calculate final confidence
                            final_confidence = base_confidence + size_confidence_boost
                            final_confidence = min(final_confidence, 100.0)

                            if final_confidence > best_confidence:
                                best_confidence = final_confidence
                                best_match = {
                                    'person': person,
                                    'confidence': final_confidence,
                                    'quality_metrics': {
                                        'base_confidence': base_confidence,
                                        'size_boost': size_confidence_boost
                                    }
                                }

                # Lower threshold for matches (75%)
                if best_match and best_confidence > 75:
                    matches.append(best_match)
                    
                    # If confidence is very high (>=90%), mark for auto-found
                    if best_confidence >= 90 and not auto_found_person:
                        auto_found_person = {
                            'person': person,
                            'confidence': best_confidence,
                            'match': best_match
                        }
            
            if matches:
                # Sort matches by confidence
                matches.sort(key=lambda x: x['confidence'], reverse=True)
                
                # If we have a very high confidence match, automatically mark as found
                if auto_found_person:
                    person = auto_found_person['person']
                    
                    # Update person status
                    person.is_found = True
                    person.date_found = datetime.utcnow()
                    
                    # Create match report
                    match_report = MatchReport(
                        missing_person_id=person.id,
                        location=request.form.get('location', 'Unknown'),
                        confidence_score=auto_found_person['confidence'],
                        photo_path=filename,
                        is_verified=True  # Auto-verify high confidence matches
                    )
                    
                    # Save changes
                    db.session.add(match_report)
                    db.session.commit()
                    
                    # Send notification email using the new function
                    if send_notification_email(person, person.date_found):
                        flash(f'High confidence match found! {person.name} has been marked as found and contact person has been notified.', 'success')
                    else:
                        flash(f'High confidence match found! {person.name} has been marked as found but there was an error sending the notification email.', 'warning')
                    
                    return redirect(url_for('found_persons'))
                
                # Show match results with accuracy information for lower confidence matches
                return render_template('match_result.html', 
                                    matches=matches, 
                                    uploaded_image=filename,
                                    auto_found=False)
            else:
                os.remove(photo_path)
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
    date_found = request.args.get('date_found', '')
    sort_by = request.args.get('sort_by', 'date_found')  # Default sort by date found

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

    if date_found:
        query = query.filter(MissingPerson.date_found == datetime.strptime(date_found, '%Y-%m-%d'))

    # Apply sorting
    if sort_by == 'date_found':
        query = query.order_by(MissingPerson.date_found.desc())
    elif sort_by == 'name':
        query = query.order_by(MissingPerson.name)
    elif sort_by == 'age':
        query = query.order_by(MissingPerson.age)
    elif sort_by == 'missing_since':
        query = query.order_by(MissingPerson.last_seen.desc())

    # Get filtered results
    found_persons = query.all()

    # Get statistics
    total_found = len(found_persons)
    found_today = len([p for p in found_persons if p.date_found.date() == datetime.now().date()])
    found_this_week = len([p for p in found_persons if (datetime.now().date() - p.date_found.date()).days <= 7])
    found_this_month = len([p for p in found_persons if p.date_found.month == datetime.now().month])

    return render_template('found_persons.html', 
                         found_persons=found_persons,
                         total_found=total_found,
                         found_today=found_today,
                         found_this_week=found_this_week,
                         found_this_month=found_this_month,
                         current_filters={
                             'age_range': age_range,
                             'gender': gender,
                             'location': location,
                             'date_found': date_found,
                             'sort_by': sort_by
                         })

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
    person = MissingPerson.query.get_or_404(id)
    
    # Update person's status
    person.is_found = False
    person.date_found = None
    person.last_seen = datetime.utcnow()  # Update last seen to current time
    person.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash(f'{person.name} has been marked as missing again.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash('Error updating person status. Please try again.', 'danger')
    
    return redirect(url_for('missing_person_detail', id=id))

@app.route('/missing_person/<int:id>/delete', methods=['POST'])
@login_required
def delete_missing_person(id):
    person = MissingPerson.query.get_or_404(id)
    try:
        # Delete all photos associated with the person
        for photo in person.photos:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.photo_path)
            if os.path.exists(photo_path):
                os.remove(photo_path)
            db.session.delete(photo)
        db.session.delete(person)
        db.session.commit()
        flash('Missing person deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting missing person: {str(e)}', 'danger')
    return redirect(url_for('missing_persons'))

@app.route('/missing_person/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_missing_person(id):
    person = MissingPerson.query.get_or_404(id)
    if request.method == 'POST':
        try:
            print("Form data received:", request.form)  # Debug log
            
            # Get form data with validation
            name = request.form.get('name', '').strip()
            if not name:
                raise ValueError("Name is required")
            
            try:
                age = int(request.form.get('age', 0))
                if age <= 0 or age > 120:
                    raise ValueError("Age must be between 1 and 120")
            except ValueError:
                raise ValueError("Invalid age value")
            
            gender = request.form.get('gender')
            if gender not in ['M', 'F']:
                raise ValueError("Invalid gender value")
            
            try:
                last_seen = datetime.strptime(request.form.get('last_seen'), '%Y-%m-%dT%H:%M')
            except ValueError:
                raise ValueError("Invalid last seen date/time")
            
            last_seen_location = request.form.get('last_seen_location', '').strip()
            if not last_seen_location:
                raise ValueError("Last seen location is required")
            
            description = request.form.get('description', '').strip()
            if not description:
                raise ValueError("Description is required")
            
            contact_name = request.form.get('contact_name', '').strip()
            if not contact_name:
                raise ValueError("Contact name is required")
            
            contact_phone = request.form.get('contact_phone', '').strip()
            if not contact_phone:
                raise ValueError("Contact phone is required")
            
            contact_email = request.form.get('contact_email', '').strip()
            if not contact_email or '@' not in contact_email:
                raise ValueError("Valid contact email is required")

            # Update person's information
            person.name = name
            person.age = age
            person.gender = gender
            person.last_seen = last_seen
            person.last_seen_location = last_seen_location
            person.description = description
            person.contact_name = contact_name
            person.contact_phone = contact_phone
            person.contact_email = contact_email
            person.updated_at = datetime.utcnow()

            # Handle multiple photo uploads
            if 'photos' in request.files:
                photos = request.files.getlist('photos')
                for photo in photos:
                    if photo and photo.filename != '':
                        if not allowed_file(photo.filename):
                            raise ValueError(f"Invalid file type for {photo.filename}. Allowed types: png, jpg, jpeg, gif")
                        
                        filename = secure_filename(photo.filename)
                        # Add timestamp to filename to prevent duplicates
                        filename = f"{int(time.time())}_{filename}"
                        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        photo.save(photo_path)

                        # Process face encoding for the new photo
                        face_encoding = process_face_encoding(photo_path)
                        if face_encoding is not None:
                            new_photo = PersonPhoto(
                                photo_path=filename,
                                face_encoding=face_encoding,
                                is_primary=(len(person.photos) == 0),  # Make primary if first photo
                                missing_person_id=person.id
                            )
                            db.session.add(new_photo)
                        else:
                            os.remove(photo_path)  # Remove photo if no face detected
                            raise ValueError(f'Could not detect a face in {photo.filename}')

            db.session.commit()
            flash('Missing person updated successfully.', 'success')
            return redirect(url_for('missing_person_detail', id=person.id))
            
        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'danger')
            print("Validation error:", str(e))  # Debug log
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating missing person: {str(e)}', 'danger')
            print("Error updating person:", str(e))  # Debug log
            
    return render_template('edit_missing_person.html', person=person)

def process_face_encoding(image_path):
    try:
        # Load the image file
        image = face_recognition.load_image_file(image_path)
        
        # Use HOG model for faster face detection
        face_locations = face_recognition.face_locations(image, model="hog")
        
        if not face_locations:
            print(f"No face detected in {image_path}")
            return None
            
        # Get face encodings with optimized parameters
        face_encodings = face_recognition.face_encodings(
            image, 
            face_locations,
            num_jitters=1,  # Reduced jitters for speed
            model="small"   # Using small model for speed
        )
        
        if not face_encodings:
            print(f"Could not encode face in {image_path}")
            return None
            
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

@app.route('/person_photo/<int:photo_id>/delete', methods=['POST'])
@login_required
def delete_person_photo(photo_id):
    photo = PersonPhoto.query.get_or_404(photo_id)
    person_id = photo.missing_person_id
    try:
        # Remove the photo file from disk
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.photo_path)
        if os.path.exists(photo_path):
            os.remove(photo_path)
        db.session.delete(photo)
        db.session.commit()
        flash('Photo deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting photo: {str(e)}', 'danger')
    return redirect(url_for('edit_missing_person', id=person_id))

@app.route('/report')
def report():
    # Get today's date
    today = datetime.now().date()
    
    # Calculate statistics for today
    today_found = MissingPerson.query.filter(db.func.date(MissingPerson.date_found) == today).count()
    today_missing = MissingPerson.query.filter(db.func.date(MissingPerson.last_seen) == today).count()
    today_registered = MissingPerson.query.filter(db.func.date(MissingPerson.last_seen) == today).count()
    
    # Get active cases (missing persons not found)
    active_cases = MissingPerson.query.filter_by(is_found=False).count()
    
    # Calculate monthly statistics
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_day = datetime.now().day
    
    # This month's statistics
    this_month_missing = MissingPerson.query.filter(
        db.extract('month', MissingPerson.last_seen) == current_month,
        db.extract('year', MissingPerson.last_seen) == current_year
    ).count()
    
    this_month_found = MissingPerson.query.filter(
        db.extract('month', MissingPerson.date_found) == current_month,
        db.extract('year', MissingPerson.date_found) == current_year
    ).count()
    
    # Calculate daily averages
    daily_avg_missing = round(this_month_missing / current_day, 1) if current_day > 0 else 0
    daily_avg_found = round(this_month_found / current_day, 1) if current_day > 0 else 0
    
    # Last month's statistics
    last_month = current_month - 1 if current_month > 1 else 12
    last_year = current_year if current_month > 1 else current_year - 1
    
    last_month_missing = MissingPerson.query.filter(
        db.extract('month', MissingPerson.last_seen) == last_month,
        db.extract('year', MissingPerson.last_seen) == last_year
    ).count()
    
    last_month_found = MissingPerson.query.filter(
        db.extract('month', MissingPerson.date_found) == last_month,
        db.extract('year', MissingPerson.date_found) == last_year
    ).count()
    
    # Calculate trends
    missing_trend = round(((this_month_missing - last_month_missing) / last_month_missing * 100), 1) if last_month_missing > 0 else 0
    found_trend = round(((this_month_found - last_month_found) / last_month_found * 100), 1) if last_month_found > 0 else 0
    
    # Calculate average response time for found cases
    found_cases = MissingPerson.query.filter(
        MissingPerson.is_found == True,
        MissingPerson.date_found != None
    ).all()
    
    total_response_time = 0
    valid_cases = 0
    
    for case in found_cases:
        if case.date_found and case.last_seen:
            response_time = (case.date_found - case.last_seen).total_seconds() / 3600  # Convert to hours
            if response_time > 0:
                total_response_time += response_time
                valid_cases += 1
    
    avg_response_time = round(total_response_time / valid_cases, 1) if valid_cases > 0 else None
    
    # Get recently found people (last 10)
    recently_found = MissingPerson.query.filter(
        MissingPerson.is_found == True
    ).order_by(
        MissingPerson.date_found.desc()
    ).limit(10).all()
    
    # Get today's new registrations
    today_registrations = MissingPerson.query.filter(
        db.func.date(MissingPerson.last_seen) == today
    ).order_by(MissingPerson.last_seen.desc()).all()
    
    # Get monthly data for charts
    monthly_missing_data = []
    monthly_found_data = []
    
    for month in range(1, 13):
        missing_count = MissingPerson.query.filter(
            db.extract('month', MissingPerson.last_seen) == month,
            db.extract('year', MissingPerson.last_seen) == current_year
        ).count()
        
        found_count = MissingPerson.query.filter(
            db.extract('month', MissingPerson.date_found) == month,
            db.extract('year', MissingPerson.date_found) == current_year
        ).count()
        
        monthly_missing_data.append(missing_count)
        monthly_found_data.append(found_count)
    
    return render_template('report.html',
                         today_found=today_found,
                         today_missing=today_missing,
                         today_registered=today_registered,
                         active_cases=active_cases,
                         this_month_missing=this_month_missing,
                         this_month_found=this_month_found,
                         last_month_missing=last_month_missing,
                         last_month_found=last_month_found,
                         avg_response_time=avg_response_time,
                         recently_found=recently_found,
                         today_registrations=today_registrations,
                         monthly_missing_data=monthly_missing_data,
                         monthly_found_data=monthly_found_data,
                         daily_avg_missing=daily_avg_missing,
                         daily_avg_found=daily_avg_found,
                         missing_trend=missing_trend,
                         found_trend=found_trend)

def send_notification_email(person, found_date=None):
    try:
        msg = Message(
            subject=f"Good News: {person.name} Has Been Found!",
            sender=app.config['MAIL_USERNAME'],
            recipients=[person.contact_email]
        )
        
        msg.body = f"""
Dear {person.contact_name},

We are pleased to inform you that {person.name} has been found!

Details:
- Name: {person.name}
- Age: {person.age}
- Found Date: {found_date.strftime('%Y-%m-%d %H:%M') if found_date else datetime.utcnow().strftime('%Y-%m-%d %H:%M')}
- Location: {person.last_seen_location}

Please contact us immediately to arrange for reunification.

Best regards,
Missing Persons System Team
"""
        mail.send(msg)
        print(f"Email sent successfully to {person.contact_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

@app.route('/missing_person/<int:id>/contact', methods=['POST'])
@login_required
def contact_found_person(id):
    try:
        person = MissingPerson.query.get_or_404(id)
        
        if send_notification_email(person):
            flash('Contact notification has been sent successfully!', 'success')
        else:
            flash('Error sending contact notification. Please try again.', 'error')
            
    except Exception as e:
        print(f"Error in contact_found_person: {str(e)}")
        flash(f'Error sending contact notification: {str(e)}', 'error')
    
    return redirect(url_for('missing_person_detail', id=id))

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {str(e)}")
    app.run(debug=True) 