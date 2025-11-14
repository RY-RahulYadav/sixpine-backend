#!/usr/bin/env python
"""
Environment setup script for Sixpine e-commerce application
"""
import os

def create_env_file():
    """Create .env file with template values"""
    env_content = """# Django Settings
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Google OAuth2 Configuration for Gmail API
# Get these from Google Cloud Console
EMAIL_CLIENT_ID=your-client-id
EMAIL_CLIENT_SECRET=your-client-secret
EMAIL_REFRESH_TOKEN=your-refresh-token

# Twilio Configuration for WhatsApp (Optional)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://sixpine-teal.vercel.app
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with template values")
        print("📝 Please update the values in .env file with your actual credentials")
    else:
        print("⚠️  .env file already exists")

def print_setup_instructions():
    """Print setup instructions"""
    print("\n" + "="*60)
    print("🚀 SIXPINE E-COMMERCE AUTHENTICATION SETUP")
    print("="*60)
    print("\n📋 SETUP STEPS:")
    print("\n1. 📧 Gmail OAuth2 Setup:")
    print("   - Go to Google Cloud Console")
    print("   - Create a project and enable Gmail API")
    print("   - Create OAuth2 credentials")
    print("   - Generate refresh token using the provided script")
    print("   - Update .env file with your credentials")
    
    print("\n2. 🔐 Email Configuration:")
    print("   - Update EMAIL_HOST_USER with your Gmail address")
    print("   - Update EMAIL_HOST_PASSWORD with your app password")
    
    print("\n3. 📱 WhatsApp Setup (Optional):")
    print("   - Sign up for Twilio account")
    print("   - Get Account SID and Auth Token")
    print("   - Update .env file with Twilio credentials")
    
    print("\n4. 🧪 Test the Setup:")
    print("   - Run: python test_gmail_oauth.py")
    print("   - Run: python test_auth.py")
    
    print("\n5. 🌐 Start the Servers:")
    print("   - Backend: python manage.py runserver")
    print("   - Frontend: cd ../client && npm run dev")
    
    print("\n" + "="*60)
    print("📚 For detailed instructions, see GMAIL_OAUTH_SETUP.md")
    print("="*60)

if __name__ == "__main__":
    create_env_file()
    print_setup_instructions()
