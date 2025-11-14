# GitHub Secrets Reference

This document lists all the GitHub secrets that need to be configured in your repository settings for the deployment workflows to work.

## Backend Secrets (server/.github/workflows/deploy.yml)

### VPS Connection
- `VPS_HOST` - Your VPS server IP address or domain
- `VPS_USER` - SSH username for VPS
- `SSH_PRIVATE_KEY` - Private SSH key for authentication

### Django Settings
- `SECRET_KEY` - Django secret key (generate a strong random string)
- `DEBUG` - Set to `False` for production
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts (e.g., `your-domain.com,www.your-domain.com,your-vps-ip`)

### Database Configuration (PostgreSQL)
- `DB_ENGINE` - Database engine: `django.db.backends.postgresql`
- `DB_NAME` - Database name (e.g., `ecommerce_db`)
- `DB_USER` - PostgreSQL username
- `DB_PASSWORD` - PostgreSQL password
- `DB_HOST` - Database host (usually `localhost` for VPS)
- `DB_PORT` - Database port (usually `5432`)
- `DB_SSLMODE` - SSL mode (optional, e.g., `prefer`, `require`, or leave empty)

### Payment Gateway
- `RAZORPAY_KEY_ID` - Razorpay API key ID
- `RAZORPAY_KEY_SECRET` - Razorpay API key secret

### Email Configuration
- `EMAIL_HOST_USER` - Gmail address for sending emails
- `EMAIL_HOST_PASSWORD` - Gmail app password (not regular password)

### Google OAuth2 (Gmail API)
- `GOOGLE_OAUTH2_CLIENT_ID` - Google OAuth2 client ID
- `GOOGLE_OAUTH2_CLIENT_SECRET` - Google OAuth2 client secret
- `GOOGLE_OAUTH2_REFRESH_TOKEN` - Google OAuth2 refresh token

### Frontend & CORS
- `FRONTEND_URL` - Frontend application URL (e.g., `https://your-frontend-domain.com`)
- `CORS_ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins (e.g., `https://your-frontend-domain.com,https://www.your-frontend-domain.com`)

### Twilio (Optional - for WhatsApp)
- `TWILIO_ACCOUNT_SID` - Twilio account SID
- `TWILIO_AUTH_TOKEN` - Twilio auth token
- `TWILIO_WHATSAPP_FROM` - Twilio WhatsApp number (e.g., `whatsapp:+14155238886`)

### Security
- `SECURE_SSL_REDIRECT` - Set to `True` for production (forces HTTPS)

## Frontend Secrets (client/.github/workflows/deploy.yml)

### API Configuration
- `VITE_API_BASE_URL` - Backend API base URL (e.g., `https://api.your-domain.com/api`)

### VPS Connection (same as backend)
- `VPS_HOST` - Your VPS server IP address or domain
- `VPS_USER` - SSH username for VPS
- `SSH_PRIVATE_KEY` - Private SSH key for authentication

## How to Add Secrets in GitHub

1. Go to your GitHub repository
2. Click on **Settings**
3. Navigate to **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret with its name and value
6. Click **Add secret**

## Important Notes

- **Never commit secrets to the repository** - Always use GitHub Secrets
- **Use strong, unique values** for `SECRET_KEY` and passwords
- **Test your deployment** after adding secrets
- **Keep secrets secure** - Don't share them publicly
- **Rotate secrets regularly** for security

## Example Secret Values

### SECRET_KEY
Generate a strong secret key:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### DEBUG
For production: `False`
For development: `True` (not recommended in production)

### ALLOWED_HOSTS
Example: `your-domain.com,www.your-domain.com,123.456.789.012`

### DB_ENGINE
Value: `django.db.backends.postgresql`

### FRONTEND_URL
Example: `https://your-frontend-domain.com`

### CORS_ALLOWED_ORIGINS
Example: `https://your-frontend-domain.com,https://www.your-frontend-domain.com`

### VITE_API_BASE_URL
Example: `https://api.your-domain.com/api` or `https://your-backend-domain.com/api`

