#!/usr/bin/env python3
"""
Seed file to create one regular user and one admin user
Run with: python seed_users.py
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from accounts.models import User

def create_users():
    """Create one regular user and one admin user"""
    
    # Regular User
    regular_user, created = User.objects.get_or_create(
        email='user@example.com',
        defaults={
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'is_staff': False,
            'is_superuser': False,
            'is_active': True,
            'is_verified': True,
        }
    )
    
    if created:
        regular_user.set_password('user123456')
        regular_user.save()
        print(f"✓ Created regular user: {regular_user.email}")
    else:
        # Update existing user
        regular_user.username = 'testuser'
        regular_user.first_name = 'Test'
        regular_user.last_name = 'User'
        regular_user.is_staff = False
        regular_user.is_superuser = False
        regular_user.is_active = True
        regular_user.set_password('user123456')
        regular_user.save()
        print(f"✓ Updated regular user: {regular_user.email}")
    
    # Admin User
    admin_user, created = User.objects.get_or_create(
        email='admin@example.com',
        defaults={
            'username': 'admin',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
            'is_verified': True,
        }
    )
    
    if created:
        admin_user.set_password('admin123456')
        admin_user.save()
        print(f"✓ Created admin user: {admin_user.email}")
    else:
        # Update existing user
        admin_user.username = 'admin'
        admin_user.first_name = 'Admin'
        admin_user.last_name = 'User'
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.set_password('admin123456')
        admin_user.save()
        print(f"✓ Updated admin user: {admin_user.email}")
    
    return regular_user, admin_user

def main():
    print("=" * 60)
    print("Creating Users")
    print("=" * 60)
    
    regular_user, admin_user = create_users()
    
    print("\n" + "=" * 60)
    print("✅ Users created successfully!")
    print("=" * 60)
    print("\nUser Credentials:")
    print("-" * 60)
    print("Regular User:")
    print(f"  Email: {regular_user.email}")
    print(f"  Username: {regular_user.username}")
    print(f"  Password: user123456")
    print(f"  Is Staff: {regular_user.is_staff}")
    print(f"  Is Superuser: {regular_user.is_superuser}")
    print("-" * 60)
    print("Admin User:")
    print(f"  Email: {admin_user.email}")
    print(f"  Username: {admin_user.username}")
    print(f"  Password: admin123456")
    print(f"  Is Staff: {admin_user.is_staff}")
    print(f"  Is Superuser: {admin_user.is_superuser}")
    print("-" * 60)

if __name__ == '__main__':
    main()

