#!/usr/bin/env python
"""
Script to upload the new Sixpine.in watermark to Cloudinary
This will replace the existing watermark with the new one
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

def upload_new_watermark():
    """Upload new Sixpine.in watermark to Cloudinary"""
    # Try multiple possible locations for the watermark
    possible_paths = [
        # New watermark location
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'client',
            'public',
            'images',
            'watermark.png'
        ),
        # Alternative: new-watermark.png
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'client',
            'public',
            'images',
            'new-watermark.png'
        ),
        # Share icon (if that's the new watermark)
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'client',
            'public',
            'share-icon.svg&quot'
        ),
    ]
    
    watermark_path = None
    for path in possible_paths:
        if os.path.exists(path):
            watermark_path = path
            print(f"Found watermark at: {watermark_path}")
            break
    
    if not watermark_path:
        print("Error: No watermark file found at any expected location")
        print("Expected locations:")
        for path in possible_paths:
            print(f"  - {path}")
        return None
    
    try:
        print(f"\nUploading new Sixpine.in watermark from {watermark_path}...")
        print("This will replace the existing 'sixpine_watermark' on Cloudinary...")
        
        # Upload watermark image to Cloudinary (overwrites existing)
        result = cloudinary.uploader.upload(
            watermark_path,
            folder='watermarks',
            public_id='sixpine_watermark',
            resource_type='image',
            overwrite=True,  # This will replace the existing watermark
            invalidate=True  # Clear CDN cache to use new watermark immediately
        )
        
        print(f"\n✓ New Sixpine.in watermark uploaded successfully!")
        print(f"  Public ID: {result['public_id']}")
        print(f"  URL: {result['secure_url']}")
        print(f"  Version: {result.get('version', 'N/A')}")
        print(f"\nThe watermark has been updated and will be automatically applied to all new image uploads!")
        print(f"No code changes needed - the watermark overlay uses 'watermarks:sixpine_watermark' which now points to your new image.")
        
        return result['public_id']
        
    except Exception as e:
        print(f"Error uploading watermark: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print("=" * 70)
    print("NEW SIXPINE.IN WATERMARK UPLOAD SCRIPT")
    print("=" * 70)
    upload_new_watermark()
    print("=" * 70)
