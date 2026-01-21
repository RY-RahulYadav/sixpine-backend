# Environment Variables Examples

## Local Development (.env)

For local development, create a `.env` file in the `server/` directory:

```env
# Django Settings
SECRET_KEY=django-insecure-your-local-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database - Leave empty to use SQLite (default for local)
# DB_ENGINE=
# DB_NAME=
# DB_USER=
# DB_PASSWORD=
# DB_HOST=
# DB_PORT=

# Email Configuration - Brevo (formerly Sendinblue)
BREVO_API_KEY=xkeysib-your-brevo-api-key-here
BREVO_SENDER_EMAIL=noreply@sixpine.in
BREVO_SENDER_NAME=Sixpine

# Admin Notification Email - Receives order confirmations
# For testing/development, use test email
ADMIN_NOTIFICATION_EMAIL=ry.rahul036@gmail.com

# Legacy Email Configuration (optional, not used - kept for backward compatibility)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Google OAuth2 Configuration
GOOGLE_OAUTH2_CLIENT_ID=your-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH2_REFRESH_TOKEN=your-refresh-token

# Razorpay Configuration
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

# Cashfree Configuration (optional)
CASHFREE_APP_ID=your-cashfree-app-id
CASHFREE_SECRET_KEY=your-cashfree-secret-key
CASHFREE_ENVIRONMENT=sandbox

# Cloudinary Configuration (for image storage)
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret

# Frontend URL
FRONTEND_URL=http://localhost:5173

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173

# Twilio Configuration (optional)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

## VPS/Production (.env)

For production on your VPS, create a `.env` file with PostgreSQL configuration:

```env
# Django Settings
SECRET_KEY=your-production-secret-key-change-this-to-random-string
DEBUG=False
ALLOWED_HOSTS=api.sixpine.in,your-domain.com,www.your-domain.com,your-vps-ip-address

# Database - PostgreSQL Settings
DB_ENGINE=django.db.backends.postgresql
DB_NAME=ecommerce_db
DB_USER=postgres_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
DB_SSLMODE=prefer

# Email Configuration - Brevo (formerly Sendinblue)
BREVO_API_KEY=xkeysib-your-brevo-production-api-key-here
BREVO_SENDER_EMAIL=noreply@sixpine.in
BREVO_SENDER_NAME=Sixpine

# Admin Notification Email - Receives order confirmations
# For production, use production admin email
ADMIN_NOTIFICATION_EMAIL=skwoodcity@gmail.com

# Legacy Email Configuration (optional, not used - kept for backward compatibility)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Google OAuth2 Configuration
GOOGLE_OAUTH2_CLIENT_ID=your-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH2_REFRESH_TOKEN=your-refresh-token

# Razorpay Configuration
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

# Cashfree Configuration (optional)
CASHFREE_APP_ID=your-cashfree-app-id
CASHFREE_SECRET_KEY=your-cashfree-secret-key
CASHFREE_ENVIRONMENT=production

# Cloudinary Configuration (for image storage)
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret

# Frontend URL (Production)
FRONTEND_URL=https://your-frontend-domain.com

# CORS Settings (Production)
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com

# Twilio Configuration (optional)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Security Settings
SECURE_SSL_REDIRECT=True
```

## Quick Setup Commands

### Local Development
```bash
# No database setup needed - SQLite will be used automatically
cd server
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### VPS/Production
```bash
# 1. Install PostgreSQL (if not installed)
sudo apt update
sudo apt install postgresql postgresql-contrib

# 2. Create database and user
sudo -u postgres psql
CREATE DATABASE ecommerce_db;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ecommerce_db TO your_username;
\q

# 3. Create .env file with PostgreSQL settings (see examples above)

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run migrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Collect static files
python manage.py collectstatic --noinput
```

## Important Notes

1. **Never commit `.env` files** - They are in `.gitignore` for security
2. **Use strong passwords** in production
3. **Keep SECRET_KEY secret** - Generate a new one for production
4. **Set DEBUG=False** in production
5. **Configure ALLOWED_HOSTS** properly for your domain

