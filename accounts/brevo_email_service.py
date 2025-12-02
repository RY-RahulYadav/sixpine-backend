import requests
import logging
from django.conf import settings

logger = logging.getLogger('accounts')


class BrevoEmailService:
    """Send emails using Brevo (formerly Sendinblue) API"""

    def __init__(self):
        self.api_key = getattr(settings, 'BREVO_API_KEY', '')
        self.api_url = 'https://api.brevo.com/v3/smtp/email'
        self.sender_email = getattr(settings, 'BREVO_SENDER_EMAIL', 'noreply@sixpine.in')
        self.sender_name = getattr(settings, 'BREVO_SENDER_NAME', 'Sixpine')
        self.last_error = None  # Store last error message for debugging

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
            self.last_error = None  # Reset error
            if not self.api_key:
                self.last_error = "Brevo API key not configured. Please set BREVO_API_KEY environment variable."
                logger.error(self.last_error)
                return False
            
            # Check if API key looks valid (should start with 'xkeysib-')
            if not self.api_key.startswith('xkeysib-'):
                logger.warning(f"Brevo API key format may be incorrect. Expected format: xkeysib-... (got: {self.api_key[:20]}...)")
            
            if not self.sender_email:
                self.last_error = "Brevo sender email not configured. Please set BREVO_SENDER_EMAIL environment variable."
                logger.error(self.last_error)
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

            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)

            if response.status_code == 201:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                error_msg = f"Error sending email: {response.status_code} - {response.text}"
                logger.error(error_msg)
                # Try to parse error details for better error message
                try:
                    error_data = response.json()
                    logger.error(f"Brevo API error details: {error_data}")
                    # Extract meaningful error message
                    if isinstance(error_data, dict):
                        if 'message' in error_data:
                            self.last_error = f"Brevo API error: {error_data['message']}"
                        elif 'error' in error_data:
                            self.last_error = f"Brevo API error: {error_data['error']}"
                        else:
                            self.last_error = f"Brevo API error (Status {response.status_code}): {str(error_data)}"
                    else:
                        self.last_error = f"Brevo API error (Status {response.status_code}): {str(error_data)}"
                except:
                    self.last_error = f"Brevo API error (Status {response.status_code}): {response.text[:200]}"
                    logger.error(f"Brevo API raw response: {response.text}")
                return False

        except requests.exceptions.Timeout:
            self.last_error = "Timeout while connecting to Brevo API. Please try again later."
            logger.error(f"Timeout while sending email to {to_email}")
            return False
        except requests.exceptions.RequestException as e:
            self.last_error = f"Network error connecting to Brevo API: {str(e)}"
            logger.error(f"Request error sending email via Brevo: {e}")
            return False
        except Exception as e:
            self.last_error = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error sending email via Brevo: {e}", exc_info=True)
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
