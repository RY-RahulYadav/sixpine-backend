#!/usr/bin/env python
"""
Script to set test passwords for all users
For testing purposes only - NEVER use in production!
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from accounts.models import User

print('=' * 100)
print(' ' * 30 + 'SETTING TEST PASSWORDS FOR ALL USERS')
print('=' * 100)
print()

# Define test passwords
test_passwords = {
    'admin@example.com': 'admin123',
    'detop53287@idwager.com': 'test123',
    'hajati1984@idwager.com': 'test123',
    'user@example.com': 'test123',
    'vendor1@example.com': 'vendor123',
    'vendor2@example.com': 'vendor123',
    'vendor3@example.com': 'vendor123',
}

# Set default password for all review users
default_review_password = 'review123'

users = User.objects.all()

for user in users:
    if user.email in test_passwords:
        password = test_passwords[user.email]
        user.set_password(password)
        user.save()
        print(f'✅ Set password for {user.email:40s} → Password: {password}')
    elif 'review' in user.email:
        user.set_password(default_review_password)
        user.save()
        print(f'✅ Set password for {user.email:40s} → Password: {default_review_password}')
    else:
        # Set default test password for any other users
        user.set_password('test123')
        user.save()
        print(f'✅ Set password for {user.email:40s} → Password: test123')

print()
print('=' * 100)
print(' ' * 35 + 'PASSWORD RESET COMPLETE!')
print('=' * 100)
print()
print('📋 QUICK REFERENCE - LOGIN CREDENTIALS:')
print()
print('=' * 100)
print('ADMIN ACCESS (Frontend + Django Admin):')
print('-' * 100)
print(f'  Email:    admin@example.com')
print(f'  Password: admin123')
print(f'  Access:   Django Admin (/admin/) + Frontend Admin Panel')
print()
print('=' * 100)
print('VENDOR ACCOUNTS (Seller/Vendor Access):')
print('-' * 100)
print(f'  1. Email: vendor1@example.com  | Password: vendor123  | Vendor: Premium Vendor (Raj Kumar)')
print(f'  2. Email: vendor2@example.com  | Password: vendor123  | Vendor: Modern Vendor (Priya Sharma)')
print(f'  3. Email: vendor3@example.com  | Password: vendor123  | Vendor: Elegant Vendor (Amit Patel)')
print()
print('=' * 100)
print('REGULAR USERS (Frontend Shopping):')
print('-' * 100)
print(f'  1. Email: user@example.com            | Password: test123')
print(f'  2. Email: detop53287@idwager.com      | Password: test123  | Name: Rahul Yadav')
print(f'  3. Email: hajati1984@idwager.com      | Password: test123  | Name: Rahul, Mobile: 9310093992')
print()
print('=' * 100)
print('REVIEW USERS (Test data - {total} users):'.format(total=users.filter(email__contains='review').count()))
print('-' * 100)
print(f'  All review users: review*@example.com  | Password: review123')
print()
print('=' * 100)
print()
print('🔐 SECURITY NOTE:')
print('   These are TEST passwords for development/testing only.')
print('   NEVER use these passwords in production!')
print()
print('=' * 100)
