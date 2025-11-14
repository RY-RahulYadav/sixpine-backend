#!/usr/bin/env python
"""
Script to seed bulk order page sections with complete data
Run with: python manage.py shell < seed_bulk_order_page_sections.py
Or: python seed_bulk_order_page_sections.py
"""

import os
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from admin_api.models import BulkOrderPageContent

def seed_bulk_order_page_sections():
    """Seed all bulk order page sections with comprehensive data"""
    
    # ==================== 1. Hero Section ====================
    hero_content = {
        'brandBadge': 'Sixpine',
        'eyebrow': 'BULK PURCHASING PROGRAM',
        'headline': 'Furnish Your Business with',
        'highlightText': 'Premium Quality',
        'subheadline': 'Special pricing, dedicated support, and customized solutions for corporate, hospitality, and large-scale residential projects. Transform your space with Sixpine\'s bulk furniture solutions.',
        'stats': [
            {'value': '50%', 'label': 'Average Savings'},
            {'value': '500+', 'label': 'Projects Completed'},
            {'value': '24/7', 'label': 'Support Available'}
        ],
        'primaryButtonText': 'Get a Quote',
        'primaryButtonLink': '#quote-form',
        'secondaryButtonText': 'Contact Sales Team',
        'secondaryButtonLink': '/contact',
        'heroImage': 'https://file.aiquickdraw.com/imgcompressed/img/compressed_6a37c6cb1e2f2462556bc01b836b7fc8.webp',
        'floatingCard': {
            'icon': '✓',
            'title': 'Premium Quality',
            'subtitle': 'Guaranteed'
        }
    }
    
    BulkOrderPageContent.objects.update_or_create(
        section_key='hero',
        defaults={
            'section_name': 'Hero Section',
            'content': hero_content,
            'is_active': True,
            'order': 1
        }
    )
    print("✓ Seeded Hero Section")
    
    # ==================== 2. Categories Section ====================
    categories_content = {
        'title': 'Industries We Serve',
        'subtitle': 'Tailored furniture solutions for every business sector',
        'categories': [
            {
                'id': 1,
                'title': 'Corporate Offices',
                'description': 'Complete office furniture solutions for modern workspaces',
                'image': 'https://file.aiquickdraw.com/imgcompressed/img/compressed_215a8341218b7c5192cd014e00644358.webp',
                'items': ['Desks & Workstations', 'Conference Tables', 'Office Chairs', 'Storage Solutions']
            },
            {
                'id': 2,
                'title': 'Hospitality',
                'description': 'Elegant furniture for hotels, restaurants, and resorts',
                'image': 'https://file.aiquickdraw.com/imgcompressed/img/compressed_6a37c6cb1e2f2462556bc01b836b7fc8.webp',
                'items': ['Guest Room Furniture', 'Lobby Seating', 'Dining Sets', 'Outdoor Furniture']
            },
            {
                'id': 3,
                'title': 'Educational Institutions',
                'description': 'Durable and functional furniture for schools and universities',
                'image': 'https://file.aiquickdraw.com/imgcompressed/img/compressed_215a8341218b7c5192cd014e00644358.webp',
                'items': ['Classroom Furniture', 'Library Shelving', 'Auditorium Seating', 'Lab Tables']
            },
            {
                'id': 4,
                'title': 'Healthcare Facilities',
                'description': 'Specialized furniture for hospitals and clinics',
                'image': 'https://file.aiquickdraw.com/imgcompressed/img/compressed_6a37c6cb1e2f2462556bc01b836b7fc8.webp',
                'items': ['Waiting Area Seating', 'Medical Cabinets', 'Patient Room Furniture', 'Staff Lounges']
            },
            {
                'id': 5,
                'title': 'Retail Spaces',
                'description': 'Custom displays and fixtures for retail environments',
                'image': 'https://file.aiquickdraw.com/imgcompressed/img/compressed_215a8341218b7c5192cd014e00644358.webp',
                'items': ['Display Units', 'Checkout Counters', 'Storage Racks', 'Seating Areas']
            },
            {
                'id': 6,
                'title': 'Residential Projects',
                'description': 'Bulk orders for apartments, condos, and housing complexes',
                'image': 'https://file.aiquickdraw.com/imgcompressed/img/compressed_6a37c6cb1e2f2462556bc01b836b7fc8.webp',
                'items': ['Living Room Sets', 'Bedroom Furniture', 'Dining Sets', 'Kitchen Cabinets']
            }
        ]
    }
    
    BulkOrderPageContent.objects.update_or_create(
        section_key='categories',
        defaults={
            'section_name': 'Categories Section',
            'content': categories_content,
            'is_active': True,
            'order': 2
        }
    )
    print("✓ Seeded Categories Section")
    
    # ==================== 3. Process Steps Section ====================
    process_content = {
        'title': 'Our Simple 6-Step Process',
        'subtitle': 'From initial quote to final installation, we make bulk ordering seamless',
        'steps': [
            {
                'id': 1,
                'number': '01',
                'title': 'Submit Your Requirements',
                'description': 'Fill out our bulk order form with your specific furniture needs, quantities, and project timeline.'
            },
            {
                'id': 2,
                'number': '02',
                'title': 'Receive Custom Quote',
                'description': 'Our team analyzes your requirements and provides a detailed quote with volume discounts within 24-48 hours.'
            },
            {
                'id': 3,
                'number': '03',
                'title': 'Consultation & Customization',
                'description': 'Work with our specialists to refine your order, select materials, colors, and finalize specifications.'
            },
            {
                'id': 4,
                'number': '04',
                'title': 'Production & Quality Check',
                'description': 'Your furniture is manufactured with premium materials and undergoes rigorous quality inspections.'
            },
            {
                'id': 5,
                'number': '05',
                'title': 'Delivery & Installation',
                'description': 'Scheduled delivery to your location with professional installation services included.'
            },
            {
                'id': 6,
                'number': '06',
                'title': 'Ongoing Support',
                'description': 'Dedicated account manager provides continued support, warranties, and maintenance services.'
            }
        ]
    }
    
    BulkOrderPageContent.objects.update_or_create(
        section_key='process',
        defaults={
            'section_name': 'Process Section',
            'content': process_content,
            'is_active': True,
            'order': 3
        }
    )
    print("✓ Seeded Process Steps Section")
    
    # ==================== 4. Benefits & Testimonials Section ====================
    benefits_content = {
        'title': 'Why Choose Our Bulk Order Service',
        'description': 'Experience these exclusive advantages when you place bulk orders with Sixpine',
        'testimonialsTitle': 'What Our Corporate Clients Say',
        'benefits': [
            {
                'id': 1,
                'title': 'Volume Discounts',
                'description': 'Special pricing with progressive discounts based on order quantity.'
            },
            {
                'id': 2,
                'title': 'Quality Guarantee',
                'description': 'All bulk orders undergo enhanced quality assurance inspections.'
            },
            {
                'id': 3,
                'title': 'Flexible Scheduling',
                'description': 'Plan deliveries according to your project timeline and needs.'
            }
        ],
        'testimonials': [
            {
                'id': 1,
                'quote': 'The bulk order process was seamless, and the dedicated support team was exceptional in handling our corporate office setup requirements.',
                'authorName': 'Ankit Bhatia',
                'authorPosition': 'Facilities Manager, TechCorp India',
                'authorInitials': 'AB'
            },
            {
                'id': 2,
                'quote': 'We furnished our entire hotel chain with Sixpine furniture. The quality, delivery timeline, and installation service exceeded our expectations.',
                'authorName': 'Priya Patel',
                'authorPosition': 'Procurement Director, Luxe Hotels',
                'authorInitials': 'PP'
            }
        ]
    }
    
    BulkOrderPageContent.objects.update_or_create(
        section_key='benefits',
        defaults={
            'section_name': 'Benefits Section',
            'content': benefits_content,
            'is_active': True,
            'order': 4
        }
    )
    print("✓ Seeded Benefits & Testimonials Section")
    
    print("\n" + "="*60)
    print("✅ All bulk order page sections seeded successfully!")
    print("📋 Sections created:")
    print("   1. Hero Section")
    print("   2. Categories Section (6 categories)")
    print("   3. Process Steps Section (6 steps)")
    print("   4. Benefits & Testimonials Section")
    print("="*60)

if __name__ == '__main__':
    seed_bulk_order_page_sections()

