#!/usr/bin/env python3
"""
Product data seed file with vendor support - Creates vendors and products with all fields populated
Run with: python seed_products_with_vendors.py
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from products.models import (
    Category, Subcategory, Color, Material, Product, ProductImage, 
    ProductVariant, ProductVariantImage, ProductSpecification, ProductFeature, ProductOffer,
    ProductReview, ProductRecommendation
)
from accounts.models import User, Vendor

def create_vendors():
    """Create sample vendors"""
    vendors = []
    
    vendor_data = [
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
        }
    ]
    
    for v_data in vendor_data:
        # Check if user exists
        user, created = User.objects.get_or_create(
            email=v_data['email'],
            defaults={
                'username': v_data['username'],
                'first_name': v_data['first_name'],
                'last_name': v_data['last_name'],
                'is_staff': True,
                'is_active': True
            }
        )
        
        if created:
            user.set_password(v_data['password'])
            user.save()
        
        # Create vendor profile
        vendor, created = Vendor.objects.get_or_create(
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
        
        vendors.append(vendor)
        print(f"✓ Created vendor: {vendor.business_name} ({vendor.brand_name})")
    
    return vendors

def create_basic_data():
    """Create basic categories, colors, materials"""
    
    # Create colors
    colors = [
        {'name': 'Red', 'hex_code': '#FF0000'},
        {'name': 'Blue', 'hex_code': '#0000FF'},
        {'name': 'Black', 'hex_code': '#000000'},
        {'name': 'White', 'hex_code': '#FFFFFF'},
        {'name': 'Brown', 'hex_code': '#8B4513'},
        {'name': 'Beige', 'hex_code': '#F5F5DC'},
        {'name': 'Grey', 'hex_code': '#808080'},
    ]
    
    color_objs = {}
    for color_data in colors:
        color, _ = Color.objects.get_or_create(
            name=color_data['name'],
            defaults={'hex_code': color_data['hex_code']}
        )
        color_objs[color_data['name']] = color
    
    # Create materials
    materials = [
        {'name': 'Solid Wood', 'description': 'High-quality solid wood construction'},
        {'name': 'Engineered Wood', 'description': 'Engineered wood with wood veneer'},
        {'name': 'Metal', 'description': 'Durable metal frame construction'},
        {'name': 'Fabric', 'description': 'Premium fabric upholstery'},
        {'name': 'Leather', 'description': 'Genuine leather upholstery'},
    ]
    
    material_objs = {}
    for material_data in materials:
        material, _ = Material.objects.get_or_create(
            name=material_data['name'],
            defaults={'description': material_data['description']}
        )
        material_objs[material_data['name']] = material
    
    # Get or create categories
    categories_data = [
        {
            'name': 'Sofas',
            'description': 'Comfortable sofas for your living room',
            'image': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=500',
            'subcategories': ['3 Seater', '2 Seater', '1 Seater']
        },
        {
            'name': 'Beds',
            'description': 'Comfortable beds for your bedroom',
            'image': 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=500',
            'subcategories': ['Queen Size Beds', 'King Size Beds', 'Single Size Beds']
        },
        {
            'name': 'Centre Tables',
            'description': 'Stylish centre tables for your living room',
            'image': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=500',
            'subcategories': ['Coffee Tables', 'Coffee Tables Set']
        },
    ]
    
    category_objs = {}
    for cat_data in categories_data:
        category, _ = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'description': cat_data['description'],
                'image': cat_data['image']
            }
        )
        category_objs[cat_data['name']] = category
        
        # Create subcategories
        for subcat_name in cat_data['subcategories']:
            Subcategory.objects.get_or_create(
                name=subcat_name,
                category=category,
                defaults={'description': f'{subcat_name} {cat_data["name"]}'}
            )
    
    return color_objs, material_objs, category_objs

def create_products(vendors, colors, materials, categories):
    """Create products with complete information including images, variants, reviews, etc."""
    
    products_data = [
        {
            'title': 'Premium 3-Seater Fabric Sofa',
            'short_description': 'Luxurious 3-seater sofa with premium fabric upholstery and modern design',
            'long_description': 'Experience ultimate comfort with our Premium 3-Seater Fabric Sofa. Crafted with attention to detail, this sofa features high-quality fabric upholstery that is both durable and comfortable. The modern design complements any living room decor while providing ample seating space for your family and guests. Perfect for entertaining or relaxing with your loved ones.',
            'category': 'Sofas',
            'subcategory': '3 Seater',
            'price': Decimal('45000.00'),
            'old_price': Decimal('55000.00'),
            'material': 'Fabric',
            'brand': 'PremiumFurn',
            'colors': ['Brown', 'Beige', 'Grey'],
            'sizes': ['Standard', 'Large', 'XL'],
            'patterns': ['Modern', 'Classic', 'Contemporary'],
            'dimensions': '220cm x 95cm x 85cm',
            'weight': '45kg',
            'warranty': '2 years',
            'is_featured': True,
            'average_rating': Decimal('4.5'),
            'review_count': 25,
            'specifications': [
                {'name': 'Brand', 'value': 'PremiumFurn'},
                {'name': 'Seating Capacity', 'value': '3 People'},
                {'name': 'Frame Material', 'value': 'Solid Wood'},
                {'name': 'Upholstery', 'value': 'Premium Fabric'},
                {'name': 'Cushion Type', 'value': 'High Density Foam'},
                {'name': 'Assembly', 'value': 'Required'},
                {'name': 'Warranty', 'value': '2 Years'},
                {'name': 'Weight Capacity', 'value': '300 kg'},
                {'name': 'Color Options', 'value': 'Brown, Beige, Grey'},
                {'name': 'Style', 'value': 'Modern Contemporary'}
            ],
            'features': [
                'Premium fabric upholstery for durability and comfort',
                'Solid wood frame construction for long-lasting use',
                'High-density foam cushions for superior comfort',
                'Modern design that complements any decor',
                'Easy to clean and maintain',
                '2-year warranty on manufacturing defects',
                'Free delivery and installation',
                '30-day return policy',
                'Scratch-resistant fabric',
                'Fire-retardant materials'
            ],
            'images': [
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800',
                'https://images.unsplash.com/photo-1506439773649-6e0eb8cfb237?w=800',
                'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800',
                'https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=800',
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800'
            ],
            'reviews': [
                {'rating': 5, 'title': 'Excellent Quality', 'comment': 'Amazing sofa! Very comfortable and looks great in our living room. Delivery was fast and assembly was easy.', 'user_name': 'Rahul Sharma'},
                {'rating': 4, 'title': 'Good Value', 'comment': 'Good quality for the price. The fabric is soft and the frame is sturdy. Would recommend.', 'user_name': 'Priya Patel'},
                {'rating': 5, 'title': 'Perfect Fit', 'comment': 'Fits perfectly in our space. The color matches our decor beautifully. Very satisfied with the purchase.', 'user_name': 'Amit Kumar'},
                {'rating': 4, 'title': 'Great Product', 'comment': 'Love the design and comfort. Assembly was straightforward. Highly recommended!', 'user_name': 'Neha Singh'},
                {'rating': 5, 'title': 'Outstanding', 'comment': 'Best sofa purchase ever! Quality is top-notch and customer service was excellent.', 'user_name': 'Rajesh Verma'}
            ]
        },
        {
            'title': 'Modern King Size Solid Wood Bed',
            'short_description': 'Elegant king size bed made from premium solid wood with modern design',
            'long_description': 'Transform your bedroom with our Modern King Size Solid Wood Bed. Crafted from premium solid wood, this bed combines traditional craftsmanship with modern design. The sturdy construction ensures years of reliable use while the elegant finish adds sophistication to your bedroom decor. Perfect for couples who value both comfort and style.',
            'category': 'Beds',
            'subcategory': 'King Size Beds',
            'price': Decimal('35000.00'),
            'old_price': Decimal('42000.00'),
            'material': 'Engineered Wood',
            'brand': 'ModernHome',
            'colors': ['Brown', 'White'],
            'sizes': ['King', 'Queen', 'Single'],
            'patterns': ['Classic', 'Modern', 'Traditional'],
            'dimensions': '198cm x 213cm x 120cm',
            'weight': '80kg',
            'warranty': '3 years',
            'is_featured': True,
            'average_rating': Decimal('4.7'),
            'review_count': 18,
            'specifications': [
                {'name': 'Brand', 'value': 'ModernHome'},
                {'name': 'Bed Size', 'value': 'King Size (198cm x 213cm)'},
                {'name': 'Material', 'value': 'Engineered Wood'},
                {'name': 'Finish', 'value': 'Matte Walnut'},
                {'name': 'Headboard', 'value': 'Included'},
                {'name': 'Assembly', 'value': 'Required'},
                {'name': 'Warranty', 'value': '3 Years'},
                {'name': 'Weight Capacity', 'value': '500 kg'},
                {'name': 'Wood Type', 'value': 'Engineered Wood'},
                {'name': 'Style', 'value': 'Contemporary'}
            ],
            'features': [
                'Premium engineered wood construction for durability',
                'Elegant matte walnut finish',
                'Sturdy headboard included',
                'Easy assembly with included tools',
                'Scratch-resistant surface',
                '3-year warranty on manufacturing defects',
                'Free delivery and installation',
                'Compatible with all standard mattresses',
                'Anti-termite treatment',
                'Eco-friendly materials'
            ],
            'images': [
                'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800',
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800',
                'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800',
                'https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=800'
            ],
            'reviews': [
                {'rating': 5, 'title': 'Solid Construction', 'comment': 'Very sturdy bed frame. The wood quality is excellent and the finish is beautiful. Assembly took some time but worth it.', 'user_name': 'Suresh Reddy'},
                {'rating': 4, 'title': 'Great Bed', 'comment': 'Good value for money. The bed is comfortable and looks great. Delivery was on time.', 'user_name': 'Anita Gupta'},
                {'rating': 5, 'title': 'Love It', 'comment': 'Perfect bed for our bedroom. The design is modern and the quality is top-notch. Highly recommended!', 'user_name': 'Vikram Joshi'},
                {'rating': 4, 'title': 'Excellent', 'comment': 'Beautiful bed with great craftsmanship. Easy to assemble and very sturdy.', 'user_name': 'Meera Iyer'},
                {'rating': 5, 'title': 'Perfect', 'comment': 'Exactly what we wanted. Great quality and fast delivery. Will buy again!', 'user_name': 'Arjun Nair'}
            ]
        },
        {
            'title': 'Elegant Coffee Table with Glass Top',
            'short_description': 'Modern coffee table with tempered glass top and metal legs',
            'long_description': 'Beautiful coffee table featuring a tempered glass top and metal legs. Perfect centerpiece for your living room. The sleek design complements modern interiors while providing a functional surface for your coffee, books, and decorative items.',
            'category': 'Centre Tables',
            'subcategory': 'Coffee Tables',
            'price': Decimal('12000.00'),
            'old_price': Decimal('15000.00'),
            'material': 'Metal',
            'brand': 'ElegantLiving',
            'colors': ['Black', 'White'],
            'sizes': ['Standard', 'Large'],
            'patterns': ['Modern', 'Minimalist'],
            'dimensions': '120cm x 60cm x 45cm',
            'weight': '15kg',
            'warranty': '1 year',
            'is_featured': False,
            'average_rating': Decimal('4.3'),
            'review_count': 15,
            'specifications': [
                {'name': 'Brand', 'value': 'ElegantLiving'},
                {'name': 'Table Top', 'value': 'Tempered Glass'},
                {'name': 'Frame Material', 'value': 'Metal'},
                {'name': 'Finish', 'value': 'Matte Black/White'},
                {'name': 'Assembly', 'value': 'Required'},
                {'name': 'Warranty', 'value': '1 Year'},
                {'name': 'Weight Capacity', 'value': '50 kg'},
                {'name': 'Glass Thickness', 'value': '8mm'},
                {'name': 'Style', 'value': 'Modern Minimalist'}
            ],
            'features': [
                'Tempered glass top for safety and durability',
                'Sturdy metal frame construction',
                'Sleek modern design',
                'Easy to clean and maintain',
                'Scratch-resistant glass surface',
                '1-year warranty on manufacturing defects',
                'Free delivery',
                'Easy assembly',
                'Space-saving design',
                'Perfect for small spaces'
            ],
            'images': [
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800',
                'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800',
                'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800'
            ],
            'reviews': [
                {'rating': 5, 'title': 'Beautiful Table', 'comment': 'Love this coffee table! It looks elegant and fits perfectly in our living room. The glass top is easy to clean.', 'user_name': 'Rohit Agarwal'},
                {'rating': 4, 'title': 'Good Quality', 'comment': 'Well-made table with good finish. Assembly was easy and the table is very stable. Happy with the purchase.', 'user_name': 'Shilpa Reddy'},
                {'rating': 5, 'title': 'Perfect Size', 'comment': 'Perfect size for our living room. The quality is excellent and it looks great. Highly recommended!', 'user_name': 'Nitin Joshi'},
                {'rating': 4, 'title': 'Great Table', 'comment': 'Good quality table. Easy to clean and maintain. Family loves it!', 'user_name': 'Pooja Iyer'}
            ]
        },
        {
            'title': 'Comfortable 2-Seater Fabric Sofa',
            'short_description': 'Compact 2-seater sofa perfect for small spaces',
            'long_description': 'Space-saving 2-seater sofa with premium fabric and comfortable cushions. Ideal for apartments and small living rooms. This sofa offers the perfect balance of comfort and style while maximizing your living space.',
            'category': 'Sofas',
            'subcategory': '2 Seater',
            'price': Decimal('28000.00'),
            'old_price': Decimal('35000.00'),
            'material': 'Fabric',
            'brand': 'PremiumFurn',
            'colors': ['Blue', 'Grey', 'Beige'],
            'sizes': ['Standard', 'Compact'],
            'patterns': ['Modern', 'Classic'],
            'dimensions': '160cm x 95cm x 85cm',
            'weight': '35kg',
            'warranty': '2 years',
            'is_featured': False,
            'average_rating': Decimal('4.4'),
            'review_count': 20,
            'specifications': [
                {'name': 'Brand', 'value': 'PremiumFurn'},
                {'name': 'Seating Capacity', 'value': '2 People'},
                {'name': 'Frame Material', 'value': 'Solid Wood'},
                {'name': 'Upholstery', 'value': 'Premium Fabric'},
                {'name': 'Cushion Type', 'value': 'High Density Foam'},
                {'name': 'Assembly', 'value': 'Required'},
                {'name': 'Warranty', 'value': '2 Years'},
                {'name': 'Weight Capacity', 'value': '200 kg'},
                {'name': 'Color Options', 'value': 'Blue, Grey, Beige'},
                {'name': 'Style', 'value': 'Modern Compact'}
            ],
            'features': [
                'Compact design perfect for small spaces',
                'Premium fabric upholstery',
                'Solid wood frame construction',
                'Comfortable high-density foam cushions',
                'Easy to clean and maintain',
                '2-year warranty on manufacturing defects',
                'Free delivery and installation',
                '30-day return policy',
                'Scratch-resistant fabric',
                'Space-saving design'
            ],
            'images': [
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800',
                'https://images.unsplash.com/photo-1506439773649-6e0eb8cfb237?w=800',
                'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800'
            ],
            'reviews': [
                {'rating': 5, 'title': 'Perfect for Small Space', 'comment': 'Exactly what we needed for our apartment. Compact yet comfortable. Great quality!', 'user_name': 'Deepak Sharma'},
                {'rating': 4, 'title': 'Good Value', 'comment': 'Good quality sofa for the price. Fits perfectly in our small living room.', 'user_name': 'Sunita Patel'},
                {'rating': 5, 'title': 'Love It', 'comment': 'Perfect size and very comfortable. The fabric is soft and the design is modern.', 'user_name': 'Ravi Kumar'},
                {'rating': 4, 'title': 'Great Sofa', 'comment': 'Good sofa for small spaces. Assembly was easy and it looks great!', 'user_name': 'Kavita Singh'}
            ]
        },
        {
            'title': 'Queen Size Storage Bed',
            'short_description': 'Queen size bed with ample storage space',
            'long_description': 'Functional queen size bed with spacious storage drawers. Made from high-quality engineered wood. This bed combines style with functionality, providing you with extra storage space while maintaining a sleek and modern appearance.',
            'category': 'Beds',
            'subcategory': 'Queen Size Beds',
            'price': Decimal('28000.00'),
            'old_price': Decimal('35000.00'),
            'material': 'Engineered Wood',
            'brand': 'ModernHome',
            'colors': ['Brown', 'White', 'Grey'],
            'sizes': ['Queen', 'King'],
            'patterns': ['Modern', 'Classic'],
            'dimensions': '152cm x 198cm x 120cm',
            'weight': '65kg',
            'warranty': '3 years',
            'is_featured': True,
            'average_rating': Decimal('4.6'),
            'review_count': 22,
            'specifications': [
                {'name': 'Brand', 'value': 'ModernHome'},
                {'name': 'Bed Size', 'value': 'Queen Size (152cm x 198cm)'},
                {'name': 'Material', 'value': 'Engineered Wood'},
                {'name': 'Storage', 'value': '4 Drawers'},
                {'name': 'Finish', 'value': 'Matte Finish'},
                {'name': 'Assembly', 'value': 'Required'},
                {'name': 'Warranty', 'value': '3 Years'},
                {'name': 'Weight Capacity', 'value': '400 kg'},
                {'name': 'Drawer Capacity', 'value': 'Large'},
                {'name': 'Style', 'value': 'Modern Functional'}
            ],
            'features': [
                'Spacious storage drawers for extra space',
                'High-quality engineered wood construction',
                'Smooth-gliding drawers',
                'Easy assembly with included tools',
                'Scratch-resistant surface',
                '3-year warranty on manufacturing defects',
                'Free delivery and installation',
                'Compatible with all standard mattresses',
                'Anti-termite treatment',
                'Eco-friendly materials'
            ],
            'images': [
                'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800',
                'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800',
                'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800',
                'https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=800'
            ],
            'reviews': [
                {'rating': 5, 'title': 'Spacious Storage', 'comment': 'Excellent bed with lots of storage space. The drawers are spacious and slide smoothly. Very happy with the purchase.', 'user_name': 'Anil Kumar'},
                {'rating': 4, 'title': 'Good Storage', 'comment': 'Good bed for the price. Plenty of space for clothes and accessories. Assembly was straightforward.', 'user_name': 'Rekha Sharma'},
                {'rating': 5, 'title': 'Love It', 'comment': 'Perfect bed for our bedroom. The quality is excellent and it looks beautiful. Worth the money!', 'user_name': 'Vijay Patel'},
                {'rating': 4, 'title': 'Great Value', 'comment': 'Good bed with ample storage. Easy to assemble and looks great!', 'user_name': 'Geeta Reddy'},
                {'rating': 5, 'title': 'Perfect', 'comment': 'Exactly what we needed. Great quality and plenty of storage space. Highly recommended!', 'user_name': 'Suresh Joshi'}
            ]
        },
    ]
    
    created_products = []
    products_with_reviews = []  # Store products with their review data
    
    for idx, prod_data in enumerate(products_data):
        # Assign vendor based on brand
        vendor = None
        for v in vendors:
            if v.brand_name == prod_data['brand']:
                vendor = v
                break
        
        if not vendor:
            vendor = vendors[idx % len(vendors)]  # Fallback to round-robin
        
        category = categories[prod_data['category']]
        subcategory = Subcategory.objects.filter(
            name=prod_data['subcategory'],
            category=category
        ).first()
        
        material = materials.get(prod_data['material'])
        
        # Generate slug from title
        from django.utils.text import slugify
        slug = slugify(prod_data['title'])
        
        # Create product
        product, created = Product.objects.get_or_create(
            title=prod_data['title'],
            defaults={
                'slug': slug,
                'short_description': prod_data['short_description'],
                'long_description': prod_data['long_description'],
                'category': category,
                'subcategory': subcategory,
                'price': prod_data['price'],
                'old_price': prod_data['old_price'],
                'material': material,
                'brand': prod_data['brand'],
                'vendor': vendor,
                'dimensions': prod_data['dimensions'],
                'weight': prod_data['weight'],
                'warranty': prod_data['warranty'],
                'is_featured': prod_data['is_featured'],
                'is_active': True,
                'main_image': prod_data['images'][0] if prod_data['images'] else 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800',
                'average_rating': prod_data.get('average_rating', Decimal('0.0')),
                'review_count': prod_data.get('review_count', 0),
                'assembly_required': True,
                'meta_title': f"{prod_data['title']} - {prod_data['brand']}",
                'meta_description': prod_data['short_description'],
            }
        )
        
        if created:
            # Add product images
            for i, img_url in enumerate(prod_data['images']):
                ProductImage.objects.create(
                    product=product,
                    image=img_url,
                    alt_text=f"{prod_data['title']} - View {i+1}",
                    sort_order=i
                )
            
            # Add specifications
            for spec in prod_data['specifications']:
                ProductSpecification.objects.create(
                    product=product,
                    name=spec['name'],
                    value=spec['value'],
                    sort_order=len(ProductSpecification.objects.filter(product=product))
                )
            
            # Add features
            for i, feature_text in enumerate(prod_data['features']):
                ProductFeature.objects.create(
                    product=product,
                    feature=feature_text,
                    sort_order=i
                )
            
            # Create variants with all combinations
            variant_count = 0
            base_price = float(product.price)
            
            for color_name in prod_data['colors']:
                color = colors.get(color_name)
                if not color:
                    continue
                    
                for size in prod_data['sizes']:
                    for pattern in prod_data['patterns']:
                        variant_title = f"{color_name} {size} {pattern}"
                        
                        # Calculate price multiplier
                        price_multiplier = 1.0
                        if 'Modern' in pattern:
                            price_multiplier = 1.1
                        elif 'Classic' in pattern:
                            price_multiplier = 0.95
                        
                        if 'XL' in size or 'King' in size:
                            price_multiplier *= 1.2
                        elif 'Large' in size or 'Queen' in size:
                            price_multiplier *= 1.1
                        
                        variant_price = round(base_price * price_multiplier, 2)
                        variant_old_price = round(base_price * price_multiplier * 1.15, 2) if product.old_price else None
                        
                        variant = ProductVariant.objects.create(
                            product=product,
                            color=color,
                            size=size,
                            pattern=pattern,
                            title=variant_title,
                            price=variant_price,
                            old_price=variant_old_price,
                            image=product.main_image,
                            stock_quantity=10,
                            is_in_stock=True,
                            is_active=True
                        )
                        
                        # Add variant images
                        variant_images = [
                            product.main_image,
                            product.images.first().image if product.images.exists() else product.main_image,
                            product.main_image
                        ]
                        
                        for idx, img_url in enumerate(variant_images):
                            if img_url:
                                ProductVariantImage.objects.create(
                                    variant=variant,
                                    image=img_url,
                                    alt_text=f"{variant_title} - Image {idx + 1}",
                                    sort_order=idx
                                )
                        
                        variant_count += 1
            
            print(f"  Created {variant_count} variants for {product.title}")
            
            # Add offers
            ProductOffer.objects.create(
                product=product,
                title='Early Bird Special',
                description='Get 15% off on your first purchase',
                discount_percentage=15,
                is_active=True
            )
            
            ProductOffer.objects.create(
                product=product,
                title='Free Delivery',
                description='Free delivery on orders above ₹20,000',
                is_active=True
            )
        
        created_products.append(product)
        # Store product with its review data
        products_with_reviews.append({
            'product': product,
            'reviews': prod_data.get('reviews', [])
        })
        print(f"✓ Created product: {product.title} (Vendor: {vendor.brand_name})")
    
    return created_products, products_with_reviews

def create_reviews_and_recommendations(products_with_reviews):
    """Create reviews and recommendations for products"""
    
    products = [item['product'] for item in products_with_reviews]
    
    # Create reviews for each product
    for item in products_with_reviews:
        product = item['product']
        review_data = item['reviews']
        
        for i, review_info in enumerate(review_data):
            # Create unique user for each review
            review_user, _ = User.objects.get_or_create(
                username=f'reviewuser_{product.id}_{i}',
                defaults={
                    'email': f'review{product.id}_{i}@example.com',
                    'first_name': review_info['user_name'].split()[0],
                    'last_name': review_info['user_name'].split()[-1] if len(review_info['user_name'].split()) > 1 else '',
                    'is_active': True
                }
            )
            ProductReview.objects.get_or_create(
                product=product,
                user=review_user,
                title=review_info['title'],
                defaults={
                    'rating': review_info['rating'],
                    'comment': review_info['comment'],
                    'is_verified_purchase': True,
                    'is_approved': True
                }
            )
    
    # Create recommendations
    recommendation_types = [
        ('buy_with', 'Buy with it'),
        ('inspired_by', 'Inspired by browsing history'),
        ('frequently_viewed', 'Frequently viewed'),
        ('similar', 'Similar products'),
        ('recommended', 'Recommended for you')
    ]
    
    for i, product in enumerate(products):
        for rec_type, rec_name in recommendation_types:
            # Get other products as recommendations
            other_products = [p for j, p in enumerate(products) if j != i]
            
            for j, rec_product in enumerate(other_products[:3]):  # Limit to 3 recommendations per type
                ProductRecommendation.objects.get_or_create(
                    product=product,
                    recommended_product=rec_product,
                    recommendation_type=rec_type,
                    defaults={
                        'sort_order': j,
                        'is_active': True
                    }
                )

def main():
    print("=" * 60)
    print("Creating Vendors and Products with Complete Information")
    print("=" * 60)
    
    # Create vendors
    print("\n1. Creating vendors...")
    vendors = create_vendors()
    print(f"   Created {len(vendors)} vendors\n")
    
    # Create basic data
    print("2. Creating categories, colors, materials...")
    colors, materials, categories = create_basic_data()
    print(f"   Created {len(colors)} colors, {len(materials)} materials, {len(categories)} categories\n")
    
    # Create products
    print("3. Creating products with complete information...")
    products, products_with_reviews = create_products(vendors, colors, materials, categories)
    print(f"   Created {len(products)} products\n")
    
    # Create reviews and recommendations
    print("4. Creating reviews and recommendations...")
    create_reviews_and_recommendations(products_with_reviews)
    print(f"   Created reviews and recommendations for {len(products)} products\n")
    
    print("=" * 60)
    print("✅ Seed data created successfully!")
    print("=" * 60)
    print(f"\nVendors created: {len(vendors)}")
    print(f"Products created: {len(products)}")
    
    # Print product details
    print("\nProduct Details:")
    for i, product in enumerate(products, 1):
        print(f"\n{i}. {product.title}")
        print(f"   Vendor: {product.vendor.brand_name}")
        print(f"   Price: ₹{product.price}")
        print(f"   Category: {product.category.name}")
        print(f"   Images: {product.images.count()}")
        print(f"   Variants: {product.variants.count()}")
        print(f"   Specifications: {product.specifications.count()}")
        print(f"   Features: {product.features.count()}")
        print(f"   Offers: {product.offers.count()}")
        print(f"   Reviews: {product.reviews.count()}")
        print(f"   Recommendations: {product.recommendations.count()}")
    
    print("\nVendor Login Credentials:")
    for vendor in vendors:
        print(f"  - {vendor.business_name}: {vendor.user.email} / vendor123456")

if __name__ == '__main__':
    main()

