from django import forms
from .models import MissingPerson, MatchReport

class MissingPersonForm(forms.ModelForm):
    class Meta:
        model = MissingPerson
        fields = [
            'name', 'age', 'gender', 'height', 'weight',
            'last_seen', 'last_seen_location', 'description',
            'photo', 'contact_name', 'contact_phone', 'contact_email'
        ]
        widgets = {
            'last_seen': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            if not photo.content_type.startswith('image/'):
                raise forms.ValidationError('Please upload an image file.')
            if photo.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('Image file size should not exceed 5MB.')
        return photo

class MatchReportForm(forms.ModelForm):
    class Meta:
        model = MatchReport
        fields = ['location', 'photo', 'confidence_score']
        widgets = {
            'confidence_score': forms.HiddenInput(),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            if not photo.content_type.startswith('image/'):
                raise forms.ValidationError('Please upload an image file.')
            if photo.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('Image file size should not exceed 5MB.')
        return photo

class MatchVerificationForm(forms.ModelForm):
    class Meta:
        model = MatchReport
        fields = ['is_verified', 'verification_notes']
        widgets = {
            'verification_notes': forms.Textarea(attrs={'rows': 4}),
        } 