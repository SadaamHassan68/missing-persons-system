from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import MissingPerson, MatchReport
from .forms import MissingPersonForm
from face_recognition.face_utils import process_image
from .notifications import NotificationService
import numpy as np
from django.http import JsonResponse

@login_required
def register_missing_person(request):
    if request.method == 'POST':
        form = MissingPersonForm(request.POST, request.FILES)
        if form.is_valid():
            missing_person = form.save(commit=False)
            
            # Process the photo to get face encoding
            if 'photo' in request.FILES:
                photo_data = request.FILES['photo'].read()
                face_encoding = process_image(photo_data)
                
                if face_encoding is not None:
                    # Convert numpy array to bytes for storage
                    missing_person.face_encoding = face_encoding.tobytes()
                    missing_person.save()
                    messages.success(request, 'Missing person registered successfully!')
                    return redirect('missing_person_detail', pk=missing_person.pk)
                else:
                    messages.error(request, 'No face detected in the photo. Please upload a clear photo of the person\'s face.')
            else:
                messages.error(request, 'Please upload a photo of the missing person.')
    else:
        form = MissingPersonForm()
    
    return render(request, 'core/register_missing_person.html', {'form': form})

@login_required
def missing_person_detail(request, pk):
    missing_person = MissingPerson.objects.get(pk=pk)
    match_reports = MatchReport.objects.filter(missing_person=missing_person)
    return render(request, 'core/missing_person_detail.html', {
        'missing_person': missing_person,
        'match_reports': match_reports
    })

@login_required
def process_video_feed(request):
    if request.method == 'POST' and 'video_frame' in request.FILES:
        frame_data = request.FILES['video_frame'].read()
        face_locations, face_encodings = process_video_frame(frame_data)
        
        if face_encodings:
            # Get all missing persons' face encodings
            missing_persons = MissingPerson.objects.filter(is_found=False)
            matches = []
            
            for missing_person in missing_persons:
                if missing_person.face_encoding:
                    known_encoding = np.frombuffer(missing_person.face_encoding, dtype=np.float64)
                    for unknown_encoding in face_encodings:
                        distance = compare_faces(known_encoding, unknown_encoding)
                        if distance <= 0.6:  # Adjust tolerance as needed
                            matches.append((missing_person, distance))
            
            if matches:
                # Sort matches by distance (closest first)
                matches.sort(key=lambda x: x[1])
                best_match = matches[0]
                
                # Create match report
                match_report = MatchReport.objects.create(
                    missing_person=best_match[0],
                    location=request.POST.get('location', 'Unknown'),
                    confidence_score=1 - best_match[1],
                    photo=request.FILES['video_frame'],
                    reported_by=request.user
                )
                
                # Send alerts
                notification_service = NotificationService()
                notification_service.create_match_alert(best_match[0], match_report)
                notification_service.send_verification_request(match_report)
                
                return JsonResponse({
                    'status': 'success',
                    'match_found': True,
                    'person_name': best_match[0].name,
                    'confidence': 1 - best_match[1]
                })
        
        return JsonResponse({'status': 'success', 'match_found': False})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def verify_match(request, match_report_id):
    match_report = MatchReport.objects.get(pk=match_report_id)
    
    if request.method == 'POST':
        is_verified = request.POST.get('is_verified') == 'true'
        verification_notes = request.POST.get('verification_notes', '')
        
        match_report.is_verified = is_verified
        match_report.verified_by = request.user
        match_report.verification_notes = verification_notes
        match_report.save()
        
        if is_verified:
            missing_person = match_report.missing_person
            missing_person.is_found = True
            missing_person.date_found = match_report.timestamp
            missing_person.save()
            
            # Send final notification
            notification_service = NotificationService()
            notification_service.create_match_alert(
                missing_person,
                match_report,
                alert_type='BOTH'
            )
        
        messages.success(request, 'Match verification completed successfully!')
        return redirect('missing_person_detail', pk=match_report.missing_person.pk)
    
    return render(request, 'core/verify_match.html', {'match_report': match_report}) 