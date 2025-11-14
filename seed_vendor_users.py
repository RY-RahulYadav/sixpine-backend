#!/usr/bin/env python3
"""
Seed file to create vendor users
Run with: python seed_vendor_users.py
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from accounts.models import User, Vendor

def create_vendor_users():
    """Create vendor users with active status"""
    
    vendors_data = [
        {
            'business_name': 'Premium Furniture Co.',
            'business_email': 'premium@furniture.com',
            'business_phone': '+919876543210',
            'business_address': '123 Furniture Street, Mumbai',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'pincode': '400001',
            'country': 'India',
            'gst_number': '27AABCU9603R1ZX',
            'pan_number': 'AABCU9603R',
            'business_type': 'Private Limited',
            'brand_name': 'PremiumFurn',
            'email': 'vendor1@example.com',
            'first_name': 'Raj',
            'last_name': 'Kumar',
            'username': 'premiumvendor',
            'password': 'vendor123456'
        },
        {
            'business_name': 'Modern Home Solutions',
            'business_email': 'modern@homesolutions.com',
            'business_phone': '+919876543211',
            'business_address': '456 Design Avenue, Delhi',
            'city': 'Delhi',
            'state': 'Delhi',
            'pincode': '110001',
            'country': 'India',
            'gst_number': '07ABCDE1234F1Z5',
            'pan_number': 'ABCDE1234F',
            'business_type': 'Sole Proprietorship',
            'brand_name': 'ModernHome',
            'email': 'vendor2@example.com',
            'first_name': 'Priya',
            'last_name': 'Sharma',
            'username': 'modernvendor',
            'password': 'vendor123456'
        },
        {
            'business_name': 'Elegant Living Furniture',
            'business_email': 'elegant@living.com',
            'business_phone': '+919876543212',
            'business_address': '789 Comfort Road, Bangalore',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'pincode': '560001',
            'country': 'India',
            'gst_number': '29FGHIJ5678K1L2',
            'pan_number': 'FGHIJ5678K',
            'business_type': 'LLC',
            'brand_name': 'ElegantLiving',
            'email': 'vendor3@example.com',
            'first_name': 'Amit',
            'last_name': 'Patel',
            'username': 'elegantvendor',
            'password': 'vendor123456'
        },
        {
            'business_name': 'Classic Wood Works',
            'business_email': 'classic@woodworks.com',
            'business_phone': '+919876543213',
            'business_address': '321 Craft Lane, Chennai',
            'city': 'Chennai',
            'state': 'Tamil Nadu',
            'pincode': '600001',
            'country': 'India',
            'gst_number': '33KLMNO9012P3Q4',
            'pan_number': 'KLMNO9012P',
            'business_type': 'Partnership',
            'brand_name': 'ClassicWood',
            'email': 'vendor4@example.com',
            'first_name': 'Suresh',
            'last_name': 'Reddy',
            'username': 'classicvendor',
            'password': 'vendor123456'
        },
        {
            'business_name': 'Urban Design Studio',
            'business_email': 'urban@designstudio.com',
            'business_phone': '+919876543214',
            'business_address': '654 Style Boulevard, Pune',
            'city': 'Pune',
            'state': 'Maharashtra',
            'pincode': '411001',
            'country': 'India',
            'gst_number': '27QRSTU3456V7W8',
            'pan_number': 'QRSTU3456V',
            'business_type': 'Private Limited',
            'brand_name': 'UrbanDesign',
            'email': 'vendor5@example.com',
            'first_name': 'Neha',
            'last_name': 'Joshi',
            'username': 'urbanvendor',
            'password': 'vendor123456'
        }
    ]
    
    created_vendors = []
    
    for v_data in vendors_data:
        # Check if user exists
        user, user_created = User.objects.get_or_create(
            email=v_data['email'],
            defaults={
                'username': v_data['username'],
                'first_name': v_data['first_name'],
                'last_name': v_data['last_name'],
                'is_staff': True,
                'is_active': True
            }
        )
        
        if user_created:
            user.set_password(v_data['password'])
            user.save()
            print(f"✓ Created user: {user.email}")
        else:
            # Update existing user
            user.username = v_data['username']
            user.first_name = v_data['first_name']
            user.last_name = v_data['last_name']
            user.is_staff = True
            user.is_active = True
            user.set_password(v_data['password'])
            user.save()
            print(f"✓ Updated user: {user.email}")
        
        # Create or update vendor profile
        vendor, vendor_created = Vendor.objects.get_or_create(
            business_email=v_data['business_email'],
            defaults={
                'user': user,
                'business_name': v_data['business_name'],
                'business_phone': v_data['business_phone'],
                'business_address': v_data['business_address'],
                'city': v_data['city'],
                'state': v_data['state'],
                'pincode': v_data['pincode'],
                'country': v_data['country'],
                'gst_number': v_data['gst_number'],
                'pan_number': v_data['pan_number'],
                'business_type': v_data['business_type'],
                'brand_name': v_data['brand_name'],
                'status': 'active',
                'is_verified': True
            }
        )
        
        if not vendor_created:
            # Update existing vendor
            vendor.user = user
            vendor.business_name = v_data['business_name']
            vendor.business_phone = v_data['business_phone']
            vendor.business_address = v_data['business_address']
            vendor.city = v_data['city']
            vendor.state = v_data['state']
            vendor.pincode = v_data['pincode']
            vendor.country = v_data['country']
            vendor.gst_number = v_data['gst_number']
            vendor.pan_number = v_data['pan_number']
            vendor.business_type = v_data['business_type']
            vendor.brand_name = v_data['brand_name']
            vendor.status = 'active'
            vendor.is_verified = True
            vendor.save()
            print(f"✓ Updated vendor: {vendor.business_name}")
        else:
            print(f"✓ Created vendor: {vendor.business_name}")
        
        created_vendors.append(vendor)
    
    return created_vendors

def main():
    print("=" * 60)
    print("Creating Vendor Users")
    print("=" * 60)
    
    vendors = create_vendor_users()
    
    print("\n" + "=" * 60)
    print("✅ Vendor users created successfully!")
    print("=" * 60)
    print(f"\nTotal vendors: {len(vendors)}")
    print("\nVendor Login Credentials:")
    print("-" * 60)
    for vendor in vendors:
        print(f"Business: {vendor.business_name}")
        print(f"  Email: {vendor.user.email}")
        print(f"  Password: vendor123456")
        print(f"  Brand: {vendor.brand_name}")
        print(f"  Status: {vendor.status}")
        print("-" * 60)

if __name__ == '__main__':
    main()

