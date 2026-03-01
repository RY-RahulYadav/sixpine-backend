#!/usr/bin/env python
"""
Script to set the admin password.
Run this script after deployment to ensure the admin password is set correctly.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

ADMIN_PASSWORD = 'sixpin@sk@woody@123321'

print('=' * 60)
print('       SETTING ADMIN PASSWORD')
print('=' * 60)

# Find all superusers / staff users
admins = User.objects.filter(is_superuser=True)

if not admins.exists():
    print('⚠️  No superuser accounts found.')
else:
    for admin in admins:
        admin.set_password(ADMIN_PASSWORD)
        admin.save()
        print(f'✅ Password updated for superuser: {admin.email or admin.username}')

print('=' * 60)
print('Done.')
