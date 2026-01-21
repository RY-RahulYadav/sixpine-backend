"""
Test script to verify Brevo email configuration and send a test order confirmation email
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from django.conf import settings
from accounts.brevo_email_service import BrevoEmailService

print("=" * 60)
print("BREVO EMAIL CONFIGURATION TEST")
print("=" * 60)

# Check settings
print("\n1. Checking Django Settings:")
print(f"   ADMIN_NOTIFICATION_EMAIL: {settings.ADMIN_NOTIFICATION_EMAIL}")
print(f"   BREVO_API_KEY: {settings.BREVO_API_KEY[:20]}... (length: {len(settings.BREVO_API_KEY)})")
print(f"   BREVO_SENDER_EMAIL: {settings.BREVO_SENDER_EMAIL}")
print(f"   BREVO_SENDER_NAME: {settings.BREVO_SENDER_NAME}")

# Test Brevo service
print("\n2. Testing Brevo Email Service:")
email_service = BrevoEmailService()
print(f"   API Key configured: {'Yes' if email_service.api_key else 'No'}")
print(f"   Sender Email: {email_service.sender_email}")
print(f"   Sender Name: {email_service.sender_name}")

# Send test email
print("\n3. Sending Test Email:")
test_email = settings.ADMIN_NOTIFICATION_EMAIL
print(f"   Sending to: {test_email}")

subject = "Sixpine - Order Email System Test"
body = "This is a test email to verify the order confirmation email system is working correctly."
html_content = """
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <div style="background-color: #232f3e; padding: 20px; color: white;">
        <h1>sixpine</h1>
    </div>
    <div style="padding: 20px;">
        <h2>Order Email System Test</h2>
        <p>This is a test email to verify the order confirmation email system is working correctly.</p>
        <p>If you receive this email, the Brevo integration is configured correctly.</p>
        <div style="background-color: #f3f3f3; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <p><strong>Configuration Details:</strong></p>
            <ul>
                <li>Admin Email: {admin_email}</li>
                <li>Sender: {sender_email}</li>
                <li>Service: Brevo API</li>
            </ul>
        </div>
        <p style="color: #666; font-size: 14px;">Test sent from Sixpine Order Confirmation System</p>
    </div>
</body>
</html>
""".format(
    admin_email=settings.ADMIN_NOTIFICATION_EMAIL,
    sender_email=settings.BREVO_SENDER_EMAIL
)

success = email_service.send_email(
    to_email=test_email,
    subject=subject,
    body=body,
    html_content=html_content
)

print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}")

if not success and hasattr(email_service, 'last_error'):
    print(f"   Error: {email_service.last_error}")

print("\n4. Testing Order Confirmation Email Function:")
try:
    from orders.email_service import send_order_confirmation_to_admin
    from orders.models import Order
    
    # Get the latest order
    latest_order = Order.objects.order_by('-created_at').first()
    
    if latest_order:
        print(f"   Testing with Order: {latest_order.order_id}")
        print(f"   Order Total: ₹{latest_order.total_amount}")
        print(f"   Customer: {latest_order.user.email}")
        
        result = send_order_confirmation_to_admin(latest_order)
        print(f"   Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    else:
        print("   No orders found in database to test with")
        
except Exception as e:
    print(f"   Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
