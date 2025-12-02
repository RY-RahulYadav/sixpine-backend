import requests
from django.conf import settings


class BrevoEmailService:
    """Send emails using Brevo (formerly Sendinblue) API"""

    def __init__(self):
        self.api_key = getattr(settings, 'BREVO_API_KEY', '')
        self.api_url = 'https://api.brevo.com/v3/smtp/email'
        self.sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', 'noreply@sixpine.in')
        self.sender_name = getattr(settings, 'BREVO_SENDER_NAME', 'Sixpine')

    def send_email(self, to_email, subject, body, html_content=None):
        """
        Send email via Brevo API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_content: Optional HTML content (if not provided, body will be used as HTML)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            if not self.api_key:
                print("❌ Brevo API key not configured")
                return False

            headers = {
                "accept": "application/json",
                "api-key": self.api_key,
                "content-type": "application/json"
            }

            payload = {
                "sender": {
                    "name": self.sender_name,
                    "email": self.sender_email
                },
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": html_content if html_content else f"<html><body><pre>{body}</pre></body></html>",
                "textContent": body
            }

            response = requests.post(self.api_url, json=payload, headers=headers)

            if response.status_code == 201:
                print(f"✅ Email sent to {to_email}")
                return True
            else:
                print(f"❌ Error sending email: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error sending email via Brevo: {e}")
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
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #ff7a00;">Sixpine - Email Verification</h2>
                <p>Dear User,</p>
                <p>Your verification code is:</p>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #ff7a00; margin: 0; font-size: 32px; letter-spacing: 5px;">{otp_code}</h1>
                </div>
                <p>This code will expire in 10 minutes.</p>
                <p>If you did not request this verification, please ignore this email.</p>
                <p>Best regards,<br>Sixpine Team</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_content)

