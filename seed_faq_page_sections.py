#!/usr/bin/env python
"""
Script to seed FAQ page sections with complete data
Run with: python manage.py shell < seed_faq_page_sections.py
Or: python seed_faq_page_sections.py
"""

import os
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from admin_api.models import FAQPageContent

def seed_faq_page_sections():
    """Seed FAQ page with comprehensive data"""
    
    # Calculate category counts based on FAQ items
    faq_items = [
        {
            'id': 1,
            'category': 'Orders',
            'q': 'How do I place an order?',
            'a': 'Browse products, add items to your cart, and proceed to checkout. During checkout you can review your order, enter shipping details and complete payment using the available payment options. You will receive a confirmation email once your order is placed successfully.'
        },
        {
            'id': 2,
            'category': 'Shipping',
            'q': 'What are the shipping options and delivery times?',
            'a': 'Shipping options vary by seller and product. At checkout you will see available shipping methods along with estimated delivery windows. Expedited shipping is available for many items. Standard delivery typically takes 5-7 business days, while express delivery is 2-3 business days.'
        },
        {
            'id': 3,
            'category': 'Returns',
            'q': 'How do I return or exchange an item?',
            'a': 'To return or exchange an item, go to Your Orders, select the order, and choose the return or exchange option. Follow the instructions and include any requested photos or details. If you need help, contact customer support. Returns are accepted within 30 days of delivery for most items.'
        },
        {
            'id': 4,
            'category': 'Orders',
            'q': 'How can I track my order?',
            'a': 'After your order ships you will receive a confirmation with tracking information. You can also check order status and tracking from Your Orders in your account. Real-time tracking updates are available 24/7 through our website and mobile app.'
        },
        {
            'id': 5,
            'category': 'Orders',
            'q': 'How do I update my account information?',
            'a': 'Go to Your Account to update your name, address, phone number, and payment methods. Keep your information current to avoid delivery issues. You can also manage your email preferences and communication settings from the account page.'
        },
        {
            'id': 6,
            'category': 'Payments',
            'q': 'What payment methods do you accept?',
            'a': 'We accept all major credit and debit cards (Visa, MasterCard, American Express), UPI payments, net banking, and digital wallets. All transactions are secured with industry-standard encryption to protect your financial information.'
        },
        {
            'id': 7,
            'category': 'Shipping',
            'q': 'Do you offer free shipping?',
            'a': 'Yes! We offer free shipping on orders above ₹999. For orders below this amount, standard shipping charges apply based on your location and the weight of your items. Premium members enjoy free shipping on all orders.'
        },
        {
            'id': 8,
            'category': 'Returns',
            'q': 'What is your return policy?',
            'a': 'We offer a 30-day return policy on most items. Products must be in original condition with tags attached. Some items like personalized furniture or clearance items may not be eligible for returns. Please check the product page for specific return eligibility.'
        },
        {
            'id': 9,
            'category': 'Payments',
            'q': 'Is it safe to use my credit card on your website?',
            'a': 'Absolutely! We use SSL encryption and PCI DSS compliant payment gateways to ensure your payment information is completely secure. We never store your complete card details on our servers.'
        },
        {
            'id': 10,
            'category': 'Shipping',
            'q': 'Can I change my delivery address after placing an order?',
            'a': 'Yes, you can change your delivery address before the order is shipped. Please contact our customer support immediately with your order number and the new address. Once the order is dispatched, address changes may not be possible.'
        }
    ]
    
    # Calculate counts for each category
    category_counts = {}
    for item in faq_items:
        category = item['category']
        category_counts[category] = category_counts.get(category, 0) + 1
    
    # Define categories with calculated counts
    categories = [
        {
            'name': 'Orders',
            'icon': '📦',
            'count': category_counts.get('Orders', 0)
        },
        {
            'name': 'Shipping',
            'icon': '🚚',
            'count': category_counts.get('Shipping', 0)
        },
        {
            'name': 'Payments',
            'icon': '💳',
            'count': category_counts.get('Payments', 0)
        },
        {
            'name': 'Returns',
            'icon': '↩️',
            'count': category_counts.get('Returns', 0)
        }
    ]
    
    # Main FAQ content structure
    faq_content = {
        'header': {
            'title': 'Frequently Asked Questions',
            'subtitle': 'Find answers to common questions about our furniture, ordering process, shipping, and more.',
            'lastUpdated': datetime.now().strftime('%B %d, %Y')
        },
        'categories': categories,
        'faqItems': faq_items
    }
    
    # Create or update FAQ page content
    faq_section, created = FAQPageContent.objects.update_or_create(
        section_key='main',
        defaults={
            'section_name': 'FAQ Page Main Content',
            'content': faq_content,
            'is_active': True,
            'order': 1
        }
    )
    
    if created:
        print("✓ Created FAQ Page Main Content")
    else:
        print("✓ Updated FAQ Page Main Content")
    
    print(f"  - Header: {faq_content['header']['title']}")
    print(f"  - Categories: {len(categories)}")
    print(f"  - FAQ Items: {len(faq_items)}")
    
    print("\n" + "="*60)
    print("✅ FAQ page sections seeded successfully!")
    print("="*60)
    print(f"\nYou can now manage FAQ content from the admin panel at:")
    print("  /admin/faq-page")
    print("\nOr via Django admin at:")
    print("  /admin/admin_api/faqpagecontent/")

if __name__ == '__main__':
    seed_faq_page_sections()

