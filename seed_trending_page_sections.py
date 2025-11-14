#!/usr/bin/env python
"""
Script to seed trending page sections with complete data
Run with: python manage.py shell < seed_trending_page_sections.py
Or: python seed_trending_page_sections.py
"""

import os
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from admin_api.models import HomePageContent
from products.models import Product

def get_first_4_products():
    """Get first 4 active products from database"""
    products = Product.objects.filter(is_active=True).order_by('id')[:4]
    product_list = []
    default_images = [
        '/images/Home/sofa1.jpg',
        '/images/Home/sofa2.jpg',
        '/images/Home/sofa3.jpg',
        '/images/Home/sofa4.jpg'
    ]
    
    for idx, product in enumerate(products):
        discount = 0
        if product.old_price and product.price:
            discount = int(((float(product.old_price) - float(product.price)) / float(product.old_price)) * 100)
        
        fallback_image = default_images[idx % len(default_images)]
        product_image = product.main_image if product.main_image and product.main_image.strip() else fallback_image
        
        product_slug = product.slug or f'product-{product.id}'
        product_data = {
            'id': product.id,
            'productId': product.id,
            'productSlug': product_slug,
            'name': product.title,
            'price': f"₹{int(product.price):,}",
            'rating': float(product.average_rating) if product.average_rating else 4.0,
            'reviewCount': product.review_count or 0,
            'image': product_image,
            'tag': 'Trending',
            'discount': f"{discount}% OFF" if discount > 0 else None,
            'navigateUrl': f'/products-details/{product_slug}',
        }
        product_list.append(product_data)
    
    # Fill with placeholder data if needed
    while len(product_list) < 4:
        idx = len(product_list) + 1
        placeholder_img = default_images[(idx - 1) % len(default_images)]
        placeholder_slug = f'product-{idx}'
        product_list.append({
            'id': idx,
            'productId': None,
            'productSlug': placeholder_slug,
            'name': f'Sample Product {idx}',
            'price': '₹9,999',
            'rating': 4.0,
            'reviewCount': 0,
            'image': placeholder_img,
            'tag': 'Trending',
            'discount': '15% OFF',
            'navigateUrl': f'/products-details/{placeholder_slug}',
        })
    
    return product_list[:4]

def seed_trending_page_sections():
    """Seed all trending page sections with comprehensive data"""
    
    # Get products for product sections
    products = get_first_4_products()
    
    # ==================== 1. Trending Products Section ====================
    trending_products_content = {
        'sectionTitle': 'Trending Right Now',
        'sectionSubtitle': 'Discover what customers are loving this week',
        'products': products,
        'viewAllButtonText': 'View All Trending Products',
        'viewAllButtonUrl': '#'
    }
    
    HomePageContent.objects.update_or_create(
        section_key='trending-products',
        defaults={
            'section_name': 'Trending Products Section',
            'content': trending_products_content,
            'is_active': True,
            'order': 1
        }
    )
    print("✓ Seeded Trending Products Section")
    
    # ==================== 2. Trending Categories Section ====================
    trending_categories_content = {
        'sectionTitle': 'Popular Trending Categories',
        'sectionSubtitle': 'Explore trending categories shoppers are loving',
        'categories': [
            {
                'id': 1,
                'name': 'Living Room',
                'image': '/images/Home/livingroom.jpg',
                'itemCount': 240,
                'trending': '+15% this week',
                'navigateUrl': '/products?category=living-room'
            },
            {
                'id': 2,
                'name': 'Bedroom',
                'image': '/images/Home/furnishing.jpg',
                'itemCount': 186,
                'trending': '+12% this week',
                'navigateUrl': '/products?category=bedroom'
            },
            {
                'id': 3,
                'name': 'Home Office',
                'image': '/images/Home/studytable.jpg',
                'itemCount': 154,
                'trending': '+28% this week',
                'navigateUrl': '/products?category=home-office'
            },
            {
                'id': 4,
                'name': 'Kitchen & Dining',
                'image': '/images/Home/furnishing.jpg',
                'itemCount': 205,
                'trending': '+8% this week',
                'navigateUrl': '/products?category=kitchen-dining'
            },
            {
                'id': 5,
                'name': 'Home Decor',
                'image': '/images/Home/livingroom.jpg',
                'itemCount': 310,
                'trending': '+20% this week',
                'navigateUrl': '/products?category=home-decor'
            },
            {
                'id': 6,
                'name': 'Outdoor Furniture',
                'image': '/images/Home/studytable.jpg',
                'itemCount': 128,
                'trending': '+5% this week',
                'navigateUrl': '/products?category=outdoor-furniture'
            }
        ]
    }
    
    HomePageContent.objects.update_or_create(
        section_key='trending-categories',
        defaults={
            'section_name': 'Trending Categories Section',
            'content': trending_categories_content,
            'is_active': True,
            'order': 2
        }
    )
    print("✓ Seeded Trending Categories Section")
    
    # ==================== 3. Trending Collections Section ====================
    trending_collections_content = {
        'analyticsTitle': "What's Hot This Week",
        'analytics': [
            {
                'id': 1,
                'name': 'Ergonomic Chairs',
                'percentage': 92
            },
            {
                'id': 2,
                'name': 'Modular Sofas',
                'percentage': 86
            },
            {
                'id': 3,
                'name': 'Minimalist Lamps',
                'percentage': 78
            },
            {
                'id': 4,
                'name': 'Smart Storage',
                'percentage': 74
            }
        ]
    }
    
    HomePageContent.objects.update_or_create(
        section_key='trending-collections',
        defaults={
            'section_name': 'Trending Collections Section',
            'content': trending_collections_content,
            'is_active': True,
            'order': 3
        }
    )
    print("✓ Seeded Trending Collections Section")
    
    print("\n" + "="*60)
    print("✅ All trending page sections seeded successfully!")
    print(f"📦 Used {len(products)} products from database")
    print("="*60)

if __name__ == '__main__':
    seed_trending_page_sections()

