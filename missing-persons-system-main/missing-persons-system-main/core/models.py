from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class MissingPerson(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    height = models.DecimalField(max_digits=5, decimal_places=2, help_text="Height in cm")
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    last_seen = models.DateTimeField()
    last_seen_location = models.CharField(max_length=200)
    description = models.TextField()
    photo = models.ImageField(upload_to='missing_persons/')
    face_encoding = models.BinaryField(null=True, blank=True)
    contact_name = models.CharField(max_length=100)
    contact_phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')]
    )
    contact_email = models.EmailField()
    is_found = models.BooleanField(default=False)
    date_found = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - Last seen: {self.last_seen}"

class MatchReport(models.Model):
    missing_person = models.ForeignKey(MissingPerson, on_delete=models.CASCADE)
    location = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    confidence_score = models.FloatField()
    photo = models.ImageField(upload_to='match_reports/')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='verified_reports')
    verification_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Match report for {self.missing_person.name} at {self.location}"

class Alert(models.Model):
    missing_person = models.ForeignKey(MissingPerson, on_delete=models.CASCADE)
    match_report = models.ForeignKey(MatchReport, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    alert_type = models.CharField(max_length=20, choices=[
        ('SMS', 'SMS'),
        ('EMAIL', 'Email'),
        ('BOTH', 'Both')
    ])
    status = models.CharField(max_length=20, choices=[
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed')
    ])
    response_received = models.BooleanField(default=False)
    response_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Alert for {self.missing_person.name} - {self.alert_type}" 