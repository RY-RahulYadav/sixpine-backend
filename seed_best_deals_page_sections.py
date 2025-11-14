#!/usr/bin/env python
"""
Script to seed best deals page sections with complete data
Run with: python manage.py shell < seed_best_deals_page_sections.py
Or: python seed_best_deals_page_sections.py
"""

import os
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from admin_api.models import HomePageContent
from products.models import Product

def get_first_8_products():
    """Get first 8 active products from database"""
    products = Product.objects.filter(is_active=True).order_by('id')[:8]
    product_list = []
    default_images = [
        '/images/Home/sofa1.jpg',
        '/images/Home/sofa2.jpg',
        '/images/Home/sofa3.jpg',
        '/images/Home/sofa4.jpg',
        '/images/Home/livingroom.jpg',
        '/images/Home/studytable.jpg',
        '/images/Home/furnishing.jpg',
        '/images/Home/sofa1.jpg'
    ]
    
    for idx, product in enumerate(products):
        discount = 0
        original_price = float(product.price) if product.price else 0
        sale_price = original_price
        
        if product.old_price and product.price:
            original_price = float(product.old_price)
            sale_price = float(product.price)
            discount = int(((original_price - sale_price) / original_price) * 100)
        
        fallback_image = default_images[idx % len(default_images)]
        product_image = product.main_image if product.main_image and product.main_image.strip() else fallback_image
        
        product_slug = product.slug or f'product-{product.id}'
        product_data = {
            'id': product.id,
            'productId': product.id,
            'name': product.title,
            'image': product_image,
            'originalPrice': f"₹{int(original_price):,}",
            'salePrice': f"₹{int(sale_price):,}",
            'discount': f"{discount}%",
            'rating': float(product.average_rating) if product.average_rating else 4.0,
            'reviewCount': product.review_count or 0,
            'soldCount': 0,
            'navigateUrl': f'/products-details/{product_slug}',
        }
        product_list.append(product_data)
    
    # Fill with placeholder data if needed
    while len(product_list) < 8:
        idx = len(product_list) + 1
        placeholder_img = default_images[(idx - 1) % len(default_images)]
        placeholder_slug = f'product-{idx}'
        product_list.append({
            'id': idx,
            'productId': None,
            'name': f'Sample Product {idx}',
            'image': placeholder_img,
            'originalPrice': '₹7,999',
            'salePrice': '₹3,999',
            'discount': '50%',
            'rating': 4.5,
            'reviewCount': 100,
            'soldCount': 50,
            'navigateUrl': f'/products-details/{placeholder_slug}',
        })
    
    return product_list[:8]

def seed_best_deals_page_sections():
    """Seed all best deals page sections with comprehensive data"""
    
    # Get products for daily deals section
    products = get_first_8_products()
    
    # ==================== 1. Deals Banner Section ====================
    deals_banner_content = {
        'banners': [
            {
                'id': 1,
                'label': 'EXCLUSIVE OFFER',
                'heading': 'Get 20% EXTRA OFF on your first purchase',
                'accentText': '20% EXTRA OFF',
                'description': 'Use code SIXPINE20 at checkout',
                'promoCode': 'SIXPINE20',
                'image': '/images/Home/livingroom.jpg',
                'buttonText': 'SHOP NOW',
                'navigateUrl': '#'
            },
            {
                'id': 2,
                'label': 'MEGA SALE',
                'heading': 'Up to 50% OFF on Furniture',
                'accentText': '50% OFF',
                'description': 'Limited time offer on selected items',
                'promoCode': 'MEGA50',
                'image': '/images/Home/studytable.jpg',
                'buttonText': 'GRAB DEALS',
                'navigateUrl': '#'
            },
            {
                'id': 3,
                'label': 'SPECIAL DEAL',
                'heading': 'Buy 2 Get 1 FREE on Home Decor',
                'accentText': 'Buy 2 Get 1 FREE',
                'description': 'Use code B2G1FREE at checkout',
                'promoCode': 'B2G1FREE',
                'image': '/images/Home/furnishing.jpg',
                'buttonText': 'EXPLORE NOW',
                'navigateUrl': '#'
            }
        ]
    }
    
    HomePageContent.objects.update_or_create(
        section_key='best-deals-banner',
        defaults={
            'section_name': 'Best Deals Banner Section',
            'content': deals_banner_content,
            'is_active': True,
            'order': 1
        }
    )
    print("✓ Seeded Best Deals Banner Section")
    
    # ==================== 2. Daily Deals Section ====================
    daily_deals_content = {
        'sectionTitle': 'Deals of the Day',
        'products': products
    }
    
    HomePageContent.objects.update_or_create(
        section_key='best-deals-daily',
        defaults={
            'section_name': 'Daily Deals Section',
            'content': daily_deals_content,
            'is_active': True,
            'order': 2
        }
    )
    print("✓ Seeded Daily Deals Section")
    
    print("\n" + "="*60)
    print("✅ All best deals page sections seeded successfully!")
    print(f"📦 Used {len(products)} products from database")
    print("="*60)

if __name__ == '__main__':
    seed_best_deals_page_sections()

