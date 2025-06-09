import face_recognition
import numpy as np
import cv2
from PIL import Image
import io

def preprocess_image(image):
    """Enhanced preprocessing for better face detection."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply histogram equalization
    gray = cv2.equalizeHist(gray)
    
    # Apply bilateral filter to reduce noise while preserving edges
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Apply adaptive histogram equalization
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    
    # Convert back to BGR
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

def get_multiple_face_encodings(image, num_samples=5):
    """Generate multiple encodings from different angles and scales."""
    encodings = []
    
    # Try original image
    locations = face_recognition.face_locations(image, model="cnn")
    if locations:
        encodings.extend(face_recognition.face_encodings(image, locations, num_jitters=2))
    
    # Try small rotations
    for angle in [-15, -10, -5, 5, 10, 15]:
        rows, cols = image.shape[:2]
        M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
        rotated = cv2.warpAffine(image, M, (cols, rows))
        locations = face_recognition.face_locations(rotated, model="cnn")
        if locations:
            encodings.extend(face_recognition.face_encodings(rotated, locations, num_jitters=2))
    
    # Try slight scaling
    for scale in [0.9, 1.1]:
        scaled = cv2.resize(image, None, fx=scale, fy=scale)
        locations = face_recognition.face_locations(scaled, model="cnn")
        if locations:
            encodings.extend(face_recognition.face_encodings(scaled, locations, num_jitters=2))
    
    return encodings

def process_image(image_data):
    """Convert image data to face encoding with enhanced processing."""
    try:
        # Convert to numpy array
        image = np.array(Image.open(io.BytesIO(image_data)).convert('RGB'))
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Apply preprocessing
        image = preprocess_image(image)
        
        # Get multiple encodings
        encodings = get_multiple_face_encodings(image)
        
        if not encodings:
            return None
            
        # Calculate weighted average of encodings
        weights = np.ones(len(encodings))
        return np.average(encodings, weights=weights, axis=0)
        
    except Exception as e:
        print(f"[ERROR] process_image: {e}")
        return None

def compare_faces(known_encoding, unknown_encoding, tolerance=0.5):
    """Enhanced face comparison with weighted distance calculation."""
    if known_encoding is None or unknown_encoding is None:
        return float('inf')
    
    # Calculate base distance
    distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
    
    # Apply confidence boosting based on distance ranges
    if distance <= tolerance * 0.5:  # Very close match
        distance *= 0.7  # 30% boost
    elif distance <= tolerance * 0.7:  # Good match
        distance *= 0.85  # 15% boost
    elif distance <= tolerance * 0.85:  # Decent match
        distance *= 0.95  # 5% boost
    
    return distance

def find_matches(unknown_encoding, known_encodings, tolerance=0.5):
    """Find best matches with enhanced confidence calculation."""
    matches = []
    for known_encoding in known_encodings:
        if known_encoding is None:
            continue
            
        dist = compare_faces(known_encoding, unknown_encoding, tolerance)
        if dist <= tolerance:
            # Calculate base confidence
            base_confidence = (1 - dist) * 100
            
            # Apply confidence boosting
            if base_confidence > 90:
                base_confidence *= 1.1  # 10% boost for very high confidence
            elif base_confidence > 80:
                base_confidence *= 1.05  # 5% boost for high confidence
            
            # Cap confidence at 100%
            final_confidence = min(base_confidence, 100.0)
            
            matches.append((known_encoding, final_confidence))
    
    # Sort by confidence
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches

def process_video_frame(frame):
    """Extract face locations and encodings from frame."""
    try:
        frame = preprocess_image(frame)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb, model="cnn")
        encodings = face_recognition.face_encodings(rgb, locations) if locations else []
        return locations, encodings
    except Exception as e:
        print(f"[ERROR] process_video_frame: {e}")
        return None, None

def draw_face_boxes(frame, face_locations, matches=None):
    """Draw bounding boxes with enhanced visualization."""
    for i, (top, right, bottom, left) in enumerate(face_locations):
        # Draw rectangle
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
        if matches and i < len(matches):
            confidence = matches[i][1]
            
            # Color coding based on confidence
            if confidence > 90:
                color = (0, 255, 0)  # Green for high confidence
            elif confidence > 80:
                color = (0, 255, 255)  # Yellow for medium confidence
            else:
                color = (0, 165, 255)  # Orange for lower confidence
            
            # Draw confidence text with background
            text = f"{confidence:.1f}%"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(frame, (left, top - text_size[1] - 10), 
                        (left + text_size[0], top), color, -1)
            cv2.putText(frame, text, (left, top - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    return frame