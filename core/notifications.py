from django.conf import settings
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from .models import Alert, MissingPerson, MatchReport

class NotificationService:
    def __init__(self):
        self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)

    def send_sms(self, to_number, message):
        """Send SMS using Twilio."""
        try:
            message = self.twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to_number
            )
            return message.sid
        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
            return None

    def send_email(self, to_email, subject, content):
        """Send email using SendGrid."""
        try:
            message = Mail(
                from_email='noreply@missingpersons.com',
                to_emails=to_email,
                subject=subject,
                html_content=content
            )
            response = self.sendgrid_client.send(message)
            return response.status_code
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return None

    def create_match_alert(self, missing_person, match_report, alert_type='BOTH'):
        """Create and send alerts for a match."""
        # Create alert record
        alert = Alert.objects.create(
            missing_person=missing_person,
            match_report=match_report,
            alert_type=alert_type,
            status='SENT'
        )

        # Prepare message content
        subject = f"Potential Match Found: {missing_person.name}"
        message = f"""
        A potential match has been found for {missing_person.name}!
        
        Location: {match_report.location}
        Time: {match_report.timestamp}
        Confidence Score: {match_report.confidence_score}
        
        Please verify this match as soon as possible.
        """

        # Send notifications based on alert type
        if alert_type in ['SMS', 'BOTH']:
            sms_sid = self.send_sms(missing_person.contact_phone, message)
            if not sms_sid:
                alert.status = 'FAILED'
                alert.save()
                return False

        if alert_type in ['EMAIL', 'BOTH']:
            email_status = self.send_email(
                missing_person.contact_email,
                subject,
                message
            )
            if not email_status or email_status >= 300:
                alert.status = 'FAILED'
                alert.save()
                return False

        alert.status = 'DELIVERED'
        alert.save()
        return True

    def send_verification_request(self, match_report):
        """Send verification request to authorities."""
        subject = "Match Verification Required"
        message = f"""
        A new match has been reported and requires verification.
        
        Missing Person: {match_report.missing_person.name}
        Location: {match_report.location}
        Time: {match_report.timestamp}
        Confidence Score: {match_report.confidence_score}
        
        Please verify this match as soon as possible.
        """

        # In a real implementation, you would send this to the appropriate authorities
        # For now, we'll just print it
        print(f"Sending verification request:\n{message}")
        return True 