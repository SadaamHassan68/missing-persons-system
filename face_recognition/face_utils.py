import face_recognition
import numpy as np
import cv2
from PIL import Image
import io

def preprocess_image(image):
    """Preprocess image for better face detection."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

def get_multiple_face_encodings(image, num_samples=3):
    """Generate multiple encodings from slightly rotated images."""
    encodings = []
    
    # Try original image
    locations = face_recognition.face_locations(image, model="cnn")
    if locations:
        encodings.extend(face_recognition.face_encodings(image, locations))
    
    # Try small rotations
    for angle in [-10, 10]:
        rows, cols = image.shape[:2]
        M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
        rotated = cv2.warpAffine(image, M, (cols, rows))
        locations = face_recognition.face_locations(rotated, model="cnn")
        if locations:
            encodings.extend(face_recognition.face_encodings(rotated, locations))

    return encodings

def process_image(image_data):
    """Convert image data to face encoding (averaged from multiple)."""
    try:
        image = np.array(Image.open(io.BytesIO(image_data)).convert('RGB'))
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        image = preprocess_image(image)
        encodings = get_multiple_face_encodings(image)
        if not encodings:
            return None
        return np.mean(encodings, axis=0)
    except Exception as e:
        print(f"[ERROR] process_image: {e}")
        return None

def compare_faces(known_encoding, unknown_encoding, tolerance=0.5):
    """Return distance between two encodings."""
    if known_encoding is None or unknown_encoding is None:
        return float('inf')
    
    distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]

    # Boost confidence slightly for very close matches
    if distance <= tolerance * 0.7:
        distance *= 0.8

    return distance

def find_matches(unknown_encoding, known_encodings, tolerance=0.5):
    """Find best matches for unknown encoding."""
    matches = []
    for known_encoding in known_encodings:
        if known_encoding is None:
            continue
        dist = compare_faces(known_encoding, unknown_encoding, tolerance)
        if dist <= tolerance:
            confidence = (1 - dist) * 100
            matches.append((known_encoding, confidence))
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
    """Draw bounding boxes and confidence if provided."""
    for i, (top, right, bottom, left) in enumerate(face_locations):
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        if matches and i < len(matches):
            confidence = matches[i][1]
            text = f"{confidence:.2f}%"
            cv2.putText(frame, text, (left, top - 8), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 255, 0), 2)
    return frame