#!/usr/bin/env python3
"""
Seed file to create default filter options for admin panel
Includes: Categories, Subcategories, Colors, Materials, and Discounts
Run with: python seed_default_filter_options.py
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from products.models import Category, Subcategory, Color, Material, Discount

def seed_colors():
    """Create default colors (5-6 colors for filter options)"""
    colors_data = [
        {'name': 'Red', 'hex_code': '#FF0000'},
        {'name': 'Blue', 'hex_code': '#0000FF'},
        {'name': 'Black', 'hex_code': '#000000'},
        {'name': 'White', 'hex_code': '#FFFFFF'},
        {'name': 'Brown', 'hex_code': '#8B4513'},
        {'name': 'Grey', 'hex_code': '#808080'},
    ]
    
    created_count = 0
    for color_data in colors_data:
        color, created = Color.objects.get_or_create(
            name=color_data['name'],
            defaults={'hex_code': color_data['hex_code']}
        )
        if created:
            created_count += 1
            print(f"✓ Created color: {color.name}")
        else:
            print(f"  Color already exists: {color.name}")
    
    return created_count

def seed_materials():
    """Create default materials"""
    materials_data = [
        {
            'name': 'Premium Fabric',
            'description': 'High-quality fabric upholstery for sofas and chairs'
        },
        {
            'name': 'Premium Leather',
            'description': 'Genuine leather upholstery for luxury furniture'
        },
        {
            'name': 'Sheesham Wood',
            'description': 'Solid Sheesham wood construction for durability'
        },
        {
            'name': 'Engineered Wood',
            'description': 'Engineered wood for modern furniture construction'
        },
        {
            'name': 'Metal Frame',
            'description': 'Sturdy metal frame construction'
        },
        {
            'name': 'Plywood',
            'description': 'High-quality plywood for furniture construction'
        }
    ]
    
    created_count = 0
    for material_data in materials_data:
        material, created = Material.objects.get_or_create(
            name=material_data['name'],
            defaults={
                'description': material_data['description'],
                'is_active': True
            }
        )
        if created:
            created_count += 1
            print(f"✓ Created material: {material.name}")
        else:
            print(f"  Material already exists: {material.name}")
    
    return created_count

def seed_discounts():
    """Create default discount filter options"""
    discounts = [10, 20, 30, 50]
    created_count = 0
    
    for pct in discounts:
        discount, created = Discount.objects.get_or_create(
            percentage=pct,
            defaults={
                'label': f'{pct}% Off',
                'is_active': True
            }
        )
        if created:
            created_count += 1
            print(f"✓ Created discount: {pct}%")
        else:
            print(f"  Discount already exists: {pct}%")
    
    return created_count

def seed_categories_and_subcategories():
    """Create default categories and subcategories"""
    categories_data = [
        {
            'name': 'Sofas',
            'description': 'Comfortable sofas for your living room',
            'subcategories': [
                '3 Seater',
                '2 Seater',
                '1 Seater',
                'Sofa Sets'
            ]
        },
        {
            'name': 'Recliners',
            'description': 'Comfortable recliners for relaxation',
            'subcategories': [
                '1 Seater Recliners',
                '2 Seater Recliners',
                '3 Seater Recliners',
                'Recliners Sets'
            ]
        },
        {
            'name': 'Rocking Chairs',
            'description': 'Classic and modern rocking chairs',
            'subcategories': [
                'Modern',
                'Relax in Motion',
                'Classic'
            ]
        },
        {
            'name': 'Beds',
            'description': 'Comfortable beds for your bedroom',
            'subcategories': [
                'Queen Size Beds',
                'King Size Beds',
                'Single Size Beds',
                'Poster Beds',
                'Folding Beds'
            ]
        },
        {
            'name': 'Centre Tables',
            'description': 'Stylish centre tables for your living room',
            'subcategories': [
                'Coffee Tables',
                'Coffee Tables Set'
            ]
        },
        {
            'name': 'Sectional Sofas',
            'description': 'Modular sectional sofas',
            'subcategories': [
                'LHS Sectionals',
                'RHS Sectionals',
                'Corner Sofas'
            ]
        },
        {
            'name': 'Chaise Loungers',
            'description': 'Comfortable chaise loungers',
            'subcategories': [
                '3 Seater Chaise Loungers',
                '2 Seater Chaise Loungers'
            ]
        },
        {
            'name': 'Chairs',
            'description': 'Various types of chairs',
            'subcategories': [
                'Arm Chairs',
                'Accent Chairs'
            ]
        },
        {
            'name': 'Sofa Cum Beds',
            'description': 'Multi-functional sofa beds',
            'subcategories': [
                'Pull Out Type',
                'Convertible Type'
            ]
        },
        {
            'name': 'Shoe Racks',
            'description': 'Organize your footwear',
            'subcategories': [
                'Shoe Cabinets',
                'Shoe Racks'
            ]
        },
        {
            'name': 'Settees & Benches',
            'description': 'Elegant settees and benches',
            'subcategories': [
                'Settees',
                'Benches'
            ]
        },
        {
            'name': 'Ottomans',
            'description': 'Versatile ottomans',
            'subcategories': [
                'Ottomans with Storage',
                'Decorative Ottomans'
            ]
        },
        {
            'name': 'Sofa Chairs',
            'description': 'Comfortable sofa chairs',
            'subcategories': [
                'Lounge Chairs',
                'Wing Chairs'
            ]
        },
        {
            'name': 'Stool & Pouffes',
            'description': 'Stylish stools and pouffes',
            'subcategories': [
                'Foot Stools',
                'Seating Stools',
                'Pouffes'
            ]
        }
    ]
    
    categories_created = 0
    subcategories_created = 0
    
    for category_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=category_data['name'],
            defaults={
                'description': category_data['description'],
                'is_active': True
            }
        )
        if created:
            categories_created += 1
            print(f"✓ Created category: {category.name}")
        else:
            print(f"  Category already exists: {category.name}")
        
        # Create subcategories
        for subcategory_name in category_data['subcategories']:
            subcategory, created = Subcategory.objects.get_or_create(
                name=subcategory_name,
                category=category,
                defaults={
                    'description': f'{subcategory_name} for {category.name.lower()}',
                    'is_active': True
                }
            )
            if created:
                subcategories_created += 1
                print(f"  ✓ Created subcategory: {category.name} - {subcategory.name}")
    
    return categories_created, subcategories_created

def main():
    print("=" * 60)
    print("Creating Default Filter Options")
    print("=" * 60)
    
    # Seed colors
    print("\n1. Seeding colors...")
    colors_count = seed_colors()
    print(f"   Created {colors_count} new colors\n")
    
    # Seed materials
    print("2. Seeding materials...")
    materials_count = seed_materials()
    print(f"   Created {materials_count} new materials\n")
    
    # Seed discounts
    print("3. Seeding discount filter options...")
    discounts_count = seed_discounts()
    print(f"   Created {discounts_count} new discount options\n")
    
    # Seed categories and subcategories
    print("4. Seeding categories and subcategories...")
    categories_count, subcategories_count = seed_categories_and_subcategories()
    print(f"   Created {categories_count} new categories and {subcategories_count} new subcategories\n")
    
    print("=" * 60)
    print("✅ Default filter options seeded successfully!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Colors: {colors_count} created")
    print(f"  - Materials: {materials_count} created")
    print(f"  - Discounts: {discounts_count} created")
    print(f"  - Categories: {categories_count} created")
    print(f"  - Subcategories: {subcategories_count} created")
    print("\nThese filter options are now available in the admin panel.")

if __name__ == '__main__':
    main()

