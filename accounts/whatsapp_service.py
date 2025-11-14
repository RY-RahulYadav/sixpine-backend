import os
from twilio.rest import Client
from django.conf import settings


class WhatsAppService:
    """Send WhatsApp messages using Twilio API"""

    def __init__(self):
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Twilio client with credentials"""
        try:
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            
            if not all([account_sid, auth_token]):
                print("Missing Twilio credentials for WhatsApp service.")
                return None
                
            self.client = Client(account_sid, auth_token)
            return self.client
            
        except Exception as e:
            print(f"Error initializing WhatsApp service: {e}")
            return None

    def send_otp_message(self, mobile_number, otp_code):
        """Send OTP via WhatsApp"""
        try:
            if not self.client:
                print("WhatsApp service not initialized")
                return False

            # Format mobile number for WhatsApp (ensure it starts with country code)
            if not mobile_number.startswith('+'):
                # Assume Indian number if no country code
                if mobile_number.startswith('0'):
                    mobile_number = '+91' + mobile_number[1:]
                elif len(mobile_number) == 10:
                    mobile_number = '+91' + mobile_number
                else:
                    mobile_number = '+' + mobile_number

            # Format for WhatsApp
            whatsapp_to = f"whatsapp:{mobile_number}"
            whatsapp_from = settings.TWILIO_WHATSAPP_FROM

            message_body = f"🔐 *Sixpine Verification*\n\nYour verification code is: *{otp_code}*\n\nThis code will expire in 10 minutes.\n\nDo not share this code with anyone."

            message = self.client.messages.create(
                body=message_body,
                from_=whatsapp_from,
                to=whatsapp_to
            )

            print(f"✅ WhatsApp OTP sent to {mobile_number} - SID: {message.sid}")
            return True

        except Exception as e:
            print(f"❌ Error sending WhatsApp OTP: {e}")
            return False

    def send_generic_message(self, mobile_number, message_text):
        """Send generic WhatsApp message"""
        try:
            if not self.client:
                print("WhatsApp service not initialized")
                return False

            # Format mobile number for WhatsApp
            if not mobile_number.startswith('+'):
                if mobile_number.startswith('0'):
                    mobile_number = '+91' + mobile_number[1:]
                elif len(mobile_number) == 10:
                    mobile_number = '+91' + mobile_number
                else:
                    mobile_number = '+' + mobile_number

            whatsapp_to = f"whatsapp:{mobile_number}"
            whatsapp_from = settings.TWILIO_WHATSAPP_FROM

            message = self.client.messages.create(
                body=message_text,
                from_=whatsapp_from,
                to=whatsapp_to
            )

            print(f"✅ WhatsApp message sent to {mobile_number} - SID: {message.sid}")
            return True

        except Exception as e:
            print(f"❌ Error sending WhatsApp message: {e}")
            return False
