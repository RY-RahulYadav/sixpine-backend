import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from django.conf import settings


class GmailOAuth2Service:
    """Send emails securely using Gmail OAuth2"""

    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    def __init__(self):
        self.service = None
        self.credentials = None

    def _get_credentials(self):
        """Load and refresh OAuth2 credentials"""
        try:
            client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
            client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET
            refresh_token = settings.GOOGLE_OAUTH2_REFRESH_TOKEN

            if not all([client_id, client_secret, refresh_token]):
                print("Missing Gmail OAuth2 credentials.")
                return None

            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=client_id,
                client_secret=client_secret
            )
            creds.refresh(Request())
            self.credentials = creds
            return creds

        except RefreshError as e:
            print(f"Token refresh failed: {e}")
            return None
        except Exception as e:
            print(f"Error getting credentials: {e}")
            return None

    def _get_service(self):
        """Build Gmail service"""
        if self.service:
            return self.service
        creds = self._get_credentials()
        if not creds:
            return None
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            return self.service
        except Exception as e:
            print(f"Error building Gmail service: {e}")
            return None

    def send_email(self, to_email, subject, body):
        """Send email via Gmail API"""
        try:
            service = self._get_service()
            if not service:
                return False

            message = MIMEText(body, "plain")
            message["to"] = to_email
            message["from"] = settings.DEFAULT_FROM_EMAIL
            message["subject"] = subject

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            service.users().messages().send(
                userId="me", body={"raw": raw_message}
            ).execute()

            print(f"✅ Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False

    def send_otp_email(self, to_email, otp_code):
        """Send OTP verification email"""
        subject = 'Sixpine - Email Verification'
        body = f"""Dear User,

Your verification code is: {otp_code}

This code will expire in 10 minutes.

If you did not request this verification, please ignore this email.

Best regards,
Sixpine Team"""
        
        return self.send_email(to_email, subject, body)
