#!/usr/bin/env python3
"""
Seed file to create navbar categories and subcategories
These are the categories displayed in the main site navigation dropdown
Run with: python seed_navbar_categories.py
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from products.models import NavbarCategory, NavbarSubcategory


def seed_navbar_categories():
    """Create navbar categories and subcategories for site navigation"""
    
    # Complete navbar categories with subcategories (matching Filter Options data)
    navbar_data = [
        {
            'name': 'Sofas',
            'sort_order': 0,
            'is_active': True,
            'subcategories': [
                {'name': '3 Seater', 'sort_order': 0},
                {'name': '2 Seater', 'sort_order': 1},
                {'name': '1 Seater', 'sort_order': 2},
                {'name': 'Sofa Sets', 'sort_order': 3},
            ]
        },
        {
            'name': 'Recliners',
            'sort_order': 1,
            'is_active': True,
            'subcategories': [
                {'name': '1 Seater Recliners', 'sort_order': 0},
                {'name': '2 Seater Recliners', 'sort_order': 1},
                {'name': '3 Seater Recliners', 'sort_order': 2},
                {'name': 'Recliners Sets', 'sort_order': 3},
            ]
        },
        {
            'name': 'Rocking Chairs',
            'sort_order': 2,
            'is_active': True,
            'subcategories': [
                {'name': 'Modern', 'sort_order': 0},
                {'name': 'Relax in Motion', 'sort_order': 1},
                {'name': 'Classic', 'sort_order': 2},
            ]
        },
        {
            'name': 'Beds',
            'sort_order': 3,
            'is_active': True,
            'subcategories': [
                {'name': 'Queen Size Beds', 'sort_order': 0},
                {'name': 'King Size Beds', 'sort_order': 1},
                {'name': 'Single Size Beds', 'sort_order': 2},
                {'name': 'Poster Beds', 'sort_order': 3},
                {'name': 'Folding Beds', 'sort_order': 4},
            ]
        },
        {
            'name': 'Centre Tables',
            'sort_order': 4,
            'is_active': True,
            'subcategories': [
                {'name': 'Coffee Tables', 'sort_order': 0},
                {'name': 'Coffee Tables Set', 'sort_order': 1},
            ]
        },
        {
            'name': 'Sectional Sofas',
            'sort_order': 5,
            'is_active': True,
            'subcategories': [
                {'name': 'LHS Sectionals', 'sort_order': 0},
                {'name': 'RHS Sectionals', 'sort_order': 1},
                {'name': 'Corner Sofas', 'sort_order': 2},
            ]
        },
        {
            'name': 'Chaise Loungers',
            'sort_order': 6,
            'is_active': True,
            'subcategories': [
                {'name': '3 Seater Chaise Loungers', 'sort_order': 0},
                {'name': '2 Seater Chaise Loungers', 'sort_order': 1},
            ]
        },
        {
            'name': 'Chairs',
            'sort_order': 7,
            'is_active': True,
            'subcategories': [
                {'name': 'Arm Chairs', 'sort_order': 0},
                {'name': 'Accent Chairs', 'sort_order': 1},
            ]
        },
        {
            'name': 'Sofa Cum Beds',
            'sort_order': 8,
            'is_active': True,
            'subcategories': [
                {'name': 'Pull Out Type', 'sort_order': 0},
                {'name': 'Convertible Type', 'sort_order': 1},
            ]
        },
        {
            'name': 'Shoe Racks',
            'sort_order': 9,
            'is_active': True,
            'subcategories': [
                {'name': 'Shoe Cabinets', 'sort_order': 0},
                {'name': 'Shoe Racks', 'sort_order': 1},
            ]
        },
        {
            'name': 'Settees & Benches',
            'sort_order': 10,
            'is_active': True,
            'subcategories': [
                {'name': 'Settees', 'sort_order': 0},
                {'name': 'Benches', 'sort_order': 1},
            ]
        },
        {
            'name': 'Ottomans',
            'sort_order': 11,
            'is_active': True,
            'subcategories': [
                {'name': 'Ottomans with Storage', 'sort_order': 0},
                {'name': 'Decorative Ottomans', 'sort_order': 1},
            ]
        },
        {
            'name': 'Sofa Chairs',
            'sort_order': 12,
            'is_active': True,
            'subcategories': [
                {'name': 'Lounge Chairs', 'sort_order': 0},
                {'name': 'Wing Chairs', 'sort_order': 1},
            ]
        },
        {
            'name': 'Stool & Pouffes',
            'sort_order': 13,
            'is_active': True,
            'subcategories': [
                {'name': 'Foot Stools', 'sort_order': 0},
                {'name': 'Seating Stools', 'sort_order': 1},
                {'name': 'Pouffes', 'sort_order': 2},
            ]
        },
    ]
    
    categories_created = 0
    categories_updated = 0
    subcategories_created = 0
    subcategories_updated = 0
    
    print("\n" + "=" * 60)
    print("🚀 Seeding Navbar Categories")
    print("=" * 60)
    
    for cat_data in navbar_data:
        subcategories_data = cat_data.pop('subcategories')
        
        # Create or update navbar category
        category, created = NavbarCategory.objects.update_or_create(
            name=cat_data['name'],
            defaults={
                'sort_order': cat_data['sort_order'],
                'is_active': cat_data['is_active'],
            }
        )
        
        if created:
            categories_created += 1
            print(f"✅ Created navbar category: {category.name}")
        else:
            categories_updated += 1
            print(f"🔄 Updated navbar category: {category.name}")
        
        # Create or update subcategories
        for sub_data in subcategories_data:
            subcategory, sub_created = NavbarSubcategory.objects.update_or_create(
                name=sub_data['name'],
                navbar_category=category,
                defaults={
                    'sort_order': sub_data['sort_order'],
                    'is_active': True,
                }
            )
            
            if sub_created:
                subcategories_created += 1
                print(f"   ✅ Created subcategory: {subcategory.name}")
            else:
                subcategories_updated += 1
                print(f"   🔄 Updated subcategory: {subcategory.name}")
    
    return categories_created, categories_updated, subcategories_created, subcategories_updated


def main():
    print("\n" + "=" * 60)
    print("📁 Navbar Categories Seed Script")
    print("=" * 60)
    print("\nThis script creates/updates navbar categories and subcategories")
    print("that appear in the main site navigation dropdown.\n")
    
    categories_created, categories_updated, subcategories_created, subcategories_updated = seed_navbar_categories()
    
    print("\n" + "=" * 60)
    print("✅ Navbar Categories Seeded Successfully!")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   Categories Created:     {categories_created}")
    print(f"   Categories Updated:     {categories_updated}")
    print(f"   Subcategories Created:  {subcategories_created}")
    print(f"   Subcategories Updated:  {subcategories_updated}")
    print(f"\n   Total Navbar Categories:    {NavbarCategory.objects.count()}")
    print(f"   Total Navbar Subcategories: {NavbarSubcategory.objects.count()}")
    print("\n📍 Manage these categories in:")
    print("   Admin Panel → Settings → Navbar Categories")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
