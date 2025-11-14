# Quick Fix: ALLOWED_HOSTS Error

If you're getting an error like:
```
Invalid HTTP_HOST header: 'api.sixpine.in'. You may need to add 'api.sixpine.in' to ALLOWED_HOSTS.
```

## Solution

You need to add `api.sixpine.in` to your `ALLOWED_HOSTS` environment variable.

### Option 1: Update GitHub Secret (Recommended for CI/CD)

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Find the `ALLOWED_HOSTS` secret
4. Edit it to include `api.sixpine.in`:
   ```
   api.sixpine.in,your-other-domains.com,www.your-other-domains.com,your-vps-ip
   ```
5. Save the secret
6. Re-run the deployment workflow

### Option 2: Update .env File on VPS (Manual Fix)

SSH into your VPS and edit the `.env` file:

```bash
cd /var/www/sixpine/backend
nano .env
```

Update the `ALLOWED_HOSTS` line to include `api.sixpine.in`:
```env
ALLOWED_HOSTS=api.sixpine.in,your-other-domains.com,www.your-other-domains.com,your-vps-ip
```

Then restart the Gunicorn service:
```bash
sudo systemctl restart gunicorn-sixpine
```

### Option 3: Quick Temporary Fix (Not Recommended for Production)

If you need a quick fix, you can temporarily allow all hosts by setting:
```env
ALLOWED_HOSTS=*
```

**Warning**: This is less secure and should only be used temporarily. Always specify your actual domains.

## Verify the Fix

After updating, test by accessing:
- `http://api.sixpine.in/docs` (should work)
- `http://api.sixpine.in/api/` (should work)

If you still get the error, make sure:
1. The `.env` file was saved correctly
2. Gunicorn was restarted
3. The environment variable is being read correctly

