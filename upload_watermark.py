#!/usr/bin/env python
"""
Script to upload watermark.png to Cloudinary
Run this script once to upload the watermark image to Cloudinary
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

import cloudinary.uploader
from ecommerce_backend.settings import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

def upload_watermark():
    """Upload watermark.png to Cloudinary"""
    watermark_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'client',
        'public',
        'images',
        'watermark.png'
    )
    
    if not os.path.exists(watermark_path):
        print(f"Error: Watermark file not found at {watermark_path}")
        return None
    
    try:
        print(f"Uploading watermark from {watermark_path}...")
        
        # Upload watermark image to Cloudinary
        result = cloudinary.uploader.upload(
            watermark_path,
            folder='watermarks',
            public_id='sixpine_watermark',
            resource_type='image',
            overwrite=True  # Overwrite if it already exists
        )
        
        print(f"✓ Watermark uploaded successfully!")
        print(f"  Public ID: {result['public_id']}")
        print(f"  URL: {result['secure_url']}")
        print(f"\nYou can now use 'sixpine_watermark' as the overlay public_id in your transformations.")
        
        return result['public_id']
        
    except Exception as e:
        print(f"Error uploading watermark: {str(e)}")
        return None

if __name__ == '__main__':
    upload_watermark()

