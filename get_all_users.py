#!/usr/bin/env python
"""
Script to display all users in the database with their details
For testing purposes only
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from accounts.models import User

print('=' * 100)
print(' ' * 35 + 'ALL USERS IN DATABASE')
print('=' * 100)
print()

users = User.objects.all().order_by('-is_superuser', '-is_staff', 'email')

for u in users:
    print(f'ID:           {u.id}')
    print(f'Email:        {u.email}')
    print(f'Username:     {u.username or "N/A"}')
    print(f'First Name:   {u.first_name or "N/A"}')
    print(f'Last Name:    {u.last_name or "N/A"}')
    print(f'Mobile:       {u.mobile or "N/A"}')
    print(f'Is Superuser: {"✅ YES (Django Admin)" if u.is_superuser else "❌ No"}')
    print(f'Is Staff:     {"✅ YES" if u.is_staff else "❌ No"}')
    print(f'Is Active:    {"✅ Active" if u.is_active else "❌ Inactive"}')
    print(f'Date Joined:  {u.date_joined.strftime("%Y-%m-%d %H:%M:%S")}')
    print('-' * 100)
    print()

print(f'Total Users: {users.count()}')
print('=' * 100)
print()
print('NOTE: Passwords are hashed and cannot be retrieved.')
print('To reset a password, use one of these commands:')
print()
print('1. Reset admin password:')
print('   python manage.py changepassword admin@example.com')
print()
print('2. Create a new superuser:')
print('   python manage.py createsuperuser')
print()
print('3. Set a specific password for testing (in Django shell):')
print('   python manage.py shell')
print('   >>> from accounts.models import User')
print('   >>> u = User.objects.get(email="admin@example.com")')
print('   >>> u.set_password("admin123")')
print('   >>> u.save()')
print('=' * 100)
