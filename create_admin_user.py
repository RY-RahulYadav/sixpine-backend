"""
Script to create an admin user for the ecommerce platform.
Run this script to create a superuser with admin privileges.
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from accounts.models import User

def create_admin_user():
    """Create an admin user"""
    print("=" * 60)
    print("Creating Admin User")
    print("=" * 60)
    
    # Default admin credentials
    username = "root@admin"
    email = "admin123@sixpine.com"
    password = "admin123"  # Change this in production!
    first_name = "Admin"
    last_name = "User"
    
    # Check if admin already exists
    if User.objects.filter(username=username).exists():
        print(f"\n⚠️  User '{username}' already exists!")
        admin_user = User.objects.get(username=username)
        
        # Update password
        admin_user.set_password(password)
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.save()
        
        print(f"✅ Updated existing admin user:")
    else:
        # Create new admin user
        admin_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_superuser=True,
            is_active=True,
            is_verified=True
        )
        print(f"✅ Created new admin user:")
    
    print(f"   Username: {admin_user.username}")
    print(f"   Email: {admin_user.email}")
    print(f"   Password: {password}")
    print(f"   Staff: {admin_user.is_staff}")
    print(f"   Superuser: {admin_user.is_superuser}")
    print(f"   Active: {admin_user.is_active}")
    print("\n" + "=" * 60)
    print("Admin Login Credentials:")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"\nYou can use these credentials to login at:")
    print(f"Frontend: http://localhost:5173/admin/login")
    print(f"API: POST http://localhost:8000/api/admin/auth/login/")
    print("=" * 60)
    print("\n⚠️  IMPORTANT: Change the password in production!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        create_admin_user()
    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

