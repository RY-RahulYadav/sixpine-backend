# Brevo IP Authorization Fix

## Issue
Your Brevo account has IP address restrictions enabled, and your current IP `2409:40d0:102c:a7b:2920:b575:56bf:1630` is not authorized.

## Solution Options

### Option 1: Add Your IP Address to Brevo (Recommended for Production)

1. Go to: https://app.brevo.com/security/authorised_ips
2. Login to your Brevo account
3. Add your current IP address: `2409:40d0:102c:a7b:2920:b575:56bf:1630`
4. Click "Save"

### Option 2: Disable IP Restrictions (For Testing/Development)

1. Go to: https://app.brevo.com/security/authorised_ips
2. Remove all IP restrictions or add `0.0.0.0/0` to allow all IPs
3. **Note**: This is less secure but easier for development

### Option 3: Use a Different API Key (Quick Fix)

If you have access to create a new API key:

1. Go to: https://app.brevo.com/settings/keys/api
2. Create a new API key
3. Make sure to select "No restrictions" or add your IP
4. Update your `.env` file with the new API key:
   ```
   BREVO_API_KEY=xkeysib-your-new-api-key-here
   ```

## Testing After Fix

Run this command to test:
```bash
cd server
python test_order_email.py
```

You should see:
```
Result: ✅ SUCCESS
```

## For Production Deployment

When deploying to production (VPS/Render/Vercel):
1. Get the server's IP address
2. Add it to Brevo authorized IPs
3. Or use an API key without IP restrictions for production

## Current Error
```
ERROR: We have detected you are using an unrecognised IP address 2409:40d0:102c:a7b:2920:b575:56bf:1630
```

This is a security feature from Brevo to prevent unauthorized access to your email API.
