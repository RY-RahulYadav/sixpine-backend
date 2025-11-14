#!/usr/bin/env python
"""
Comprehensive script to seed all homepage sections with complete data
Run with: python manage.py shell < seed_homepage_all_sections.py
Or: python seed_homepage_all_sections.py
"""

import os
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from admin_api.models import HomePageContent
from products.models import Product

def get_first_6_products():
    """Get first 6 active products from database"""
    products = Product.objects.filter(is_active=True).order_by('id')[:6]
    product_list = []
    # Default fallback images that exist in the project
    default_images = [
        '/images/Home/sofa1.jpg',
        '/images/Home/sofa2.jpg',
        '/images/Home/sofa3.jpg',
        '/images/Home/sofa4.jpg',
        '/images/Home/bed.jpg',
        '/images/Home/bedroom.jpg'
    ]
    
    for idx, product in enumerate(products):
        # Calculate discount percentage
        discount = 0
        if product.old_price and product.price:
            discount = int(((float(product.old_price) - float(product.price)) / float(product.old_price)) * 100)
        
        # Use product image if available, otherwise use default image from list
        fallback_image = default_images[idx % len(default_images)]
        product_image = product.main_image if product.main_image and product.main_image.strip() else fallback_image
        
        product_data = {
            'id': product.id,
            'productId': product.id,
            'productSlug': product.slug or f'product-{product.id}',
            'title': product.title,
            'subtitle': product.short_description[:50] if product.short_description else '',
            'image': product_image,  # Use 'image' for Discover & Top Rated sections
            'img': product_image,  # Also keep 'img' for banner cards
            'desc': (product.short_description[:100] if product.short_description else ''),
            'rating': float(product.average_rating) if product.average_rating else 4.0,
            'reviews': product.review_count or 0,
            'price': f"₹{int(product.price):,}",
            'oldPrice': f"₹{int(product.old_price):,}" if product.old_price else None,
            'newPrice': f"₹{int(product.price):,}",
            'discount': f"{discount}% off" if discount > 0 else None,
        }
        product_list.append(product_data)
    
    # If less than 6 products exist, fill with placeholder data
    while len(product_list) < 6:
        idx = len(product_list) + 1
        placeholder_img = default_images[(idx - 1) % len(default_images)]
        product_list.append({
            'id': idx,
            'productId': None,
            'productSlug': f'product-{idx}',
            'title': f'Sample Product {idx}',
            'subtitle': 'Sample subtitle',
            'image': placeholder_img,
            'img': placeholder_img,
            'desc': 'Sample product description',
            'rating': 4.0,
            'reviews': 0,
            'price': '₹9,999',
            'oldPrice': '₹14,999',
            'newPrice': '₹9,999',
            'discount': '33% off',
        })
    
    return product_list[:6]  # Return exactly 6

def seed_all_homepage_sections():
    """Seed all homepage sections with comprehensive data"""
    
    # Get first 6 products for product selectors
    products = get_first_6_products()
    
    # ==================== 1. Hero Section ====================
    hero_content = {
        'slides': [
            {
                'id': 1,
                'title': 'Be the Perfect Host',
                'subtitle': 'Coffee Table',
                'price': '₹ 2,499',
                'buttonText': 'BUY NOW',
                'backgroundColor': '#C4A484',
                'imageSrc': '/images/Home/studytable.jpg'
            },
            {
                'id': 2,
                'title': 'Comfort Redefined',
                'subtitle': 'Sofa Collection',
                'price': '₹ 15,999',
                'buttonText': 'BUY NOW',
                'backgroundColor': '#8B7355',
                'imageSrc': '/images/Home/furnishing.jpg'
            },
            {
                'id': 3,
                'title': 'Sleep in Style',
                'subtitle': 'Bedroom Sets',
                'price': '₹ 25,999',
                'buttonText': 'BUY NOW',
                'backgroundColor': '#A68B5B',
                'imageSrc': '/images/Home/bedroom.jpg'
            }
        ],
        'specialDealBanner': {
            'badgeText': 'SPECIAL DEAL',
            'uptoText': 'UPTO',
            'discountText': '₹5000 OFF',
            'instantDiscountText': 'INSTANT DISCOUNT',
            'buttonText': 'BUY NOW',
            'backgroundImage': '/images/Home/bedroomPanel.webp'
        },
        'mattressBanner': {
            'badgeText': 'Ships in 2 Days',
            'badgeIcon': 'truck',
            'title': 'MATTRESS',
            'subtitle': 'That Turns Sleep into Therapy',
            'startingText': 'Starting From',
            'price': '₹9,999',
            'deliveryText': 'FREE Delivery Available',
            'backgroundImage': '/images/metress.png'
        },
        'bottomBanner': {
            'imageUrl': 'https://ii1.pepperfry.com/assets/a08eed1c-bbbd-4e8b-b381-07df5fbfe959.jpg',
            'altText': 'Sixpine Banner'
        }
    }
    
    HomePageContent.objects.update_or_create(
        section_key='hero',
        defaults={
            'section_name': 'Hero Section',
            'content': hero_content,
            'is_active': True,
            'order': 1
        }
    )
    print("✓ Seeded Hero Section")
    
    # ==================== 2. Hero Section 2 ====================
    hero2_content = {
        'sections': [
            {
                'id': 1,
                'title': 'Pick up where you left off',
                'linkText': 'See more',
                'linkUrl': '#',
                'items': [
                    {'id': 1, 'imageUrl': '/images/Home/sofa1.jpg', 'text': 'Sixpine Premium', 'altText': 'Sofa'},
                    {'id': 2, 'imageUrl': '/images/Home/sofa2.jpg', 'text': 'LEGACY OF COMFORT...', 'altText': 'Sofa'},
                    {'id': 3, 'imageUrl': '/images/Home/sofa3.jpg', 'text': 'LEGACY OF COMFORT...', 'altText': 'Sofa'},
                    {'id': 4, 'imageUrl': '/images/Home/sofa4.jpg', 'text': 'LEGACY OF COMFORT...', 'altText': 'Sofa'}
                ]
            },
            {
                'id': 2,
                'title': 'New home arrivals under $50',
                'linkText': 'Shop the latest from Home',
                'linkUrl': '#',
                'isSpecial': True,
                'items': [
                    {'id': 1, 'imageUrl': '/images/Home/Cookware1.jpg', 'text': 'Kitchen & Dining', 'altText': 'Cookware'},
                    {'id': 2, 'imageUrl': '/images/Home/Cans.jpg', 'text': 'Home Improvement', 'altText': 'Cans'},
                    {'id': 3, 'imageUrl': '/images/Home/Decor.jpg', 'text': 'Décor', 'altText': 'Decor'},
                    {'id': 4, 'imageUrl': '/images/Home/Pillow.jpg', 'text': 'Bedding & Bath', 'altText': 'Pillow'}
                ]
            },
            {
                'id': 3,
                'title': 'Up to 60% off | Furniture & mattresses',
                'linkText': 'Explore all',
                'linkUrl': '#',
                'items': [
                    {'id': 1, 'imageUrl': '/images/Home/sofa4.jpg', 'text': 'Mattresses & more', 'altText': 'Mattress'},
                    {'id': 2, 'imageUrl': '/images/Home/sofa3.jpg', 'text': 'Office chairs & more', 'altText': 'Chair'},
                    {'id': 3, 'imageUrl': '/images/Home/sofa2.jpg', 'text': 'Sofas & more', 'altText': 'Sofa'},
                    {'id': 4, 'imageUrl': '/images/Home/sofa1.jpg', 'text': 'Bean bags & more', 'altText': 'Bean bag'}
                ]
            },
            {
                'id': 4,
                'title': 'More items to consider',
                'linkText': 'See more',
                'linkUrl': '#',
                'isSpecial': True,
                'items': [
                    {'id': 1, 'imageUrl': '/images/Home/1.webp', 'text': 'MosQuick® Stainless st...', 'altText': 'Clip1'},
                    {'id': 2, 'imageUrl': '/images/Home/2.webp', 'text': 'FDSHIP Stainless Stee...', 'altText': 'Clip2'},
                    {'id': 3, 'imageUrl': '/images/Home/3.webp', 'text': 'WEWEL® Premium Stai...', 'altText': 'Clip3'},
                    {'id': 4, 'imageUrl': '/images/Home/4.webp', 'text': 'Marita Heavy Duty Clot...', 'altText': 'Clip4'}
                ]
            }
        ]
    }
    
    HomePageContent.objects.update_or_create(
        section_key='hero2',
        defaults={
            'section_name': 'Hero Section 2',
            'content': hero2_content,
            'is_active': True,
            'order': 2
        }
    )
    print("✓ Seeded Hero Section 2")
    
    # ==================== 3. Hero Section 3 ====================
    hero3_content = {
        'title': "Beautify Every Corner with Elegance",
        'subtitle': "Explore timeless pieces for every nook and space",
        'offerBadge': "UPTO 60% OFF",
        'leftProductCard': {
            'name': "Light Show",
            'img': "/images/Home/FloorLamps.jpg"
        },
        'categoryItems': [
            {'id': 1, 'name': "Floor Lamps", 'img': "/images/Home/FloorLamps.jpg"},
            {'id': 2, 'name': "Hanging Lights", 'img': "/images/Home/HangingLights.jpg"},
            {'id': 3, 'name': "Home Temple", 'img': "/images/Home/HomeTemple.webp"},
            {'id': 4, 'name': "Serving Trays", 'img': "/images/Home/ServingTrays.jpg"},
            {'id': 5, 'name': "Wall Decor", 'img': "/images/Home/Decor.jpg"},
            {'id': 6, 'name': "Kitchen Racks", 'img': "/images/Home/Cookware.jpg"},
            {'id': 7, 'name': "Chopping Board", 'img': "/images/Home/ServingTrays.jpg"},
            {'id': 8, 'name': "Artificial Plants", 'img': "/images/Home/FloorLamps.jpg"}
        ],
        'sliderCards': [
            {
                'id': 1,
                'tag': "UPTO 45% OFF",
                'title': "TV UNIT",
                'desc': "Built to Hold the Drama",
                'price': "₹1,800",
                'img': "/images/Home/sofa1.jpg",
            },
            {
                'id': 2,
                'tag': "UPTO 50% OFF",
                'title': "OFFICE CHAIR",
                'desc': "Built to Hold the Drama",
                'price': "₹3,989",
                'img': "/images/Home/sofa4.jpg",
            },
            {
                'id': 3,
                'tag': "UPTO 40% OFF",
                'title': "HOME TEMPLE",
                'desc': "Built to Hold the Drama",
                'price': "₹3,000",
                'img': "/images/Home/sofa2.jpg",
            }
        ]
    }
    
    HomePageContent.objects.update_or_create(
        section_key='hero3',
        defaults={
            'section_name': 'Hero Section 3',
            'content': hero3_content,
            'is_active': True,
            'order': 3
        }
    )
    print("✓ Seeded Hero Section 3")
    
    # ==================== 4. Furniture Categories ====================
    categories_content = {
        'sectionTitle': "Shop By Categories",
        'filterButtons': ["All", "Living", "Bedroom", "Dining", "Mattress", "Decor", "Study"],
        'categories': [
            {'id': 1, 'title': "Sofas", 'category': "Living", 'img': "/images/Home/sofa1.jpg"},
            {'id': 2, 'title': "Beds", 'category': "Bedroom", 'img': "/images/Home/bedroom.jpg"},
            {'id': 3, 'title': "Dining", 'category': "Dining", 'img': "/images/Home/dining.jpg"},
            {'id': 4, 'title': "Tv units", 'category': "Living", 'img': "/images/Home/tv.jpg"},
            {'id': 5, 'title': "Coffee tables", 'category': "Living", 'img': "/images/Home/coffee.jpg"},
            {'id': 6, 'title': "Cabinets", 'category': "Living", 'img': "/images/Home/cabinet.jpg"},
            {'id': 7, 'title': "Mattresses", 'category': "Mattress", 'img': "/images/Home/mattress.jpg"},
            {'id': 8, 'title': "Wardrobes", 'category': "Bedroom", 'img': "/images/Home/wardrobe.jpg"},
            {'id': 9, 'title': "Sofa cum bed", 'category': "Bedroom", 'img': "/images/Home/sofacumbed.jpg"},
            {'id': 10, 'title': "Bookshelves", 'category': "Decor", 'img': "/images/Home/bookshelf.jpg"},
            {'id': 11, 'title': "All study tables", 'category': "Study", 'img': "/images/Home/studytable.jpg"},
            {'id': 12, 'title': "Home furnishing", 'category': "Decor", 'img': "/images/Home/furnishing.jpg"}
        ],
        'sliderTitle': "India's Finest Online Furniture Brand",
        'shortDescription': "Buy Furniture Online from our extensive collection of wooden furniture units to give your home an elegant touch at affordable prices.",
        'fullDescription': "Buy Furniture Online from our extensive collection of wooden furniture units to give your home an elegant touch at affordable prices. We offer a wide range of Lorem ipsum dolor sit amet consectetur adipisicing elit. Ducimus deleniti dolor a aspernatur esse necessitatibus nihil blanditiis repellat ipsa ut praesentium qui, neque quidem soluta earum impedit eveniet corrupti fugit.",
        'sliderItems': [
            {'id': 1, 'title': "Living Room", 'img': "/images/Home/livingroom.jpg", 'url': ""},
            {'id': 2, 'title': "Bedroom", 'img': "/images/Home/bedroom.jpg", 'url': ""},
            {'id': 3, 'title': "Dining Room", 'img': "/images/Home/diningroom.jpg", 'url': ""},
            {'id': 4, 'title': "Study", 'img': "/images/Home/studytable.jpg", 'url': ""},
            {'id': 5, 'title': "Outdoor", 'img': "/images/Home/outdoor.jpg", 'url': ""},
            {'id': 6, 'title': "Living Room", 'img': "/images/Home/livingroom.jpg", 'url': ""},
            {'id': 7, 'title': "Bedroom", 'img': "/images/Home/bedroom.jpg", 'url': ""},
            {'id': 8, 'title': "Dining Room", 'img': "/images/Home/diningroom.jpg", 'url': ""}
        ]
    }
    
    HomePageContent.objects.update_or_create(
        section_key='categories',
        defaults={
            'section_name': 'Shop By Categories',
            'content': categories_content,
            'is_active': True,
            'order': 4
        }
    )
    print("✓ Seeded Furniture Categories")
    
    # ==================== 5. Furniture Sections (Discover & Top Rated) ====================
    # Format products for Discover & Top Rated sections (need full product structure)
    discover_products = []
    top_rated_products = []
    
    for product in products[:6]:
        # Format for Discover & Top Rated sections
        formatted_product = {
            'id': product.get('id', product.get('productId', 0)),
            'title': product.get('title', ''),
            'subtitle': product.get('subtitle', product.get('desc', '')[:100]),
            'price': product.get('price', product.get('newPrice', '₹0')),
            'oldPrice': product.get('oldPrice', ''),
            'discount': product.get('discount', ''),
            'rating': product.get('rating', 4.0),
            'reviews': product.get('reviews', 0),
            'image': product.get('image', product.get('img', '/images/Home/sofa1.jpg')),
            'productId': product.get('productId'),
            'productSlug': product.get('productSlug', '#')
        }
        discover_products.append(formatted_product)
        top_rated_products.append(formatted_product)
    
    furniture_sections_content = {
        'discover': {
            'title': "Discover what's new",
            'subtitle': "Designed to refresh your everyday life",
            'products': discover_products
        },
        'topRated': {
            'title': "Top-Rated by Indian Homes",
            'subtitle': "Crafted to complement Indian lifestyles",
            'products': top_rated_products
        }
    }
    
    HomePageContent.objects.update_or_create(
        section_key='furniture-sections',
        defaults={
            'section_name': 'Discover & Top Rated Sections',
            'content': furniture_sections_content,
            'is_active': True,
            'order': 5
        }
    )
    print("✓ Seeded Furniture Sections (Discover & Top Rated)")
    
    # ==================== 6. Furniture Offer Sections ====================
    # Create product images with navigation URLs from first 6 products
    offer_products_1 = []
    offer_products_2 = []
    offer_products_3 = []
    
    # Default images for offer sections
    offer_default_images = [
        '/images/Home/sofa1.jpg',
        '/images/Home/sofa2.jpg',
        '/images/Home/sofa3.jpg',
        '/images/Home/sofa4.jpg',
        '/images/Home/bed.jpg',
        '/images/Home/bedroom.jpg',
        '/images/Home/chair.jpg'
    ]
    
    for i, product in enumerate(products[:7]):
        # Use product image if available, otherwise use default
        product_img = product.get('img', offer_default_images[i % len(offer_default_images)])
        if i < 3:
            offer_products_1.append({
                'imageUrl': product_img,
                'navigateUrl': f"/products-details/{product.get('productSlug', '#')}" if product.get('productSlug') else '#'
            })
        elif i < 6:
            offer_products_2.append({
                'imageUrl': product_img,
                'navigateUrl': f"/products-details/{product.get('productSlug', '#')}" if product.get('productSlug') else '#'
            })
        else:
            offer_products_3.append({
                'imageUrl': product_img,
                'navigateUrl': f"/products-details/{product.get('productSlug', '#')}" if product.get('productSlug') else '#'
            })
    
    # Fill remaining slots with default images if needed
    while len(offer_products_1) < 7:
        idx = len(offer_products_1)
        offer_products_1.append({
            'imageUrl': offer_default_images[idx % len(offer_default_images)],
            'navigateUrl': '#'
        })
    while len(offer_products_2) < 6:
        idx = len(offer_products_2)
        offer_products_2.append({
            'imageUrl': offer_default_images[idx % len(offer_default_images)],
            'navigateUrl': '#'
        })
    while len(offer_products_3) < 6:
        idx = len(offer_products_3)
        offer_products_3.append({
            'imageUrl': offer_default_images[idx % len(offer_default_images)],
            'navigateUrl': '#'
        })
    
    furniture_offer_content = {
        'sections': [
            {
                'id': 1,
                'title': "Up to 60% Off | Furniture crafted for every corner",
                'link': "See all offers",
                'linkUrl': "#",
                'products': offer_products_1
            },
            {
                'id': 2,
                'title': "Sofa for living room",
                'link': "See more",
                'linkUrl': "#",
                'products': offer_products_2
            },
            {
                'id': 3,
                'title': "Related to items you've viewed",
                'link': "See more",
                'linkUrl': "#",
                'products': offer_products_3
            }
        ]
    }
    
    HomePageContent.objects.update_or_create(
        section_key='furniture-offer-sections',
        defaults={
            'section_name': 'Furniture Offer Sections',
            'content': furniture_offer_content,
            'is_active': True,
            'order': 6
        }
    )
    print("✓ Seeded Furniture Offer Sections")
    
    # ==================== 7. Feature Card & CTA ====================
    # Calculate countdown end date (30 days from now)
    countdown_end = datetime.now() + timedelta(days=30)
    
    feature_card_content = {
        'featuresBar': [
            {'icon': "Store", 'count': "100+", 'text': "Experience Stores Across<br/>India"},
            {'icon': "Truck", 'count': "350+", 'text': "Delivery Centers<br/>Across India"},
            {'icon': "ThumbsUp", 'count': "10 Lakh +", 'text': "Satisfied Customers"},
            {'icon': "BadgeDollarSign", 'count': "Lowest Price", 'text': "Guarantee"},
            {'icon': "Shield", 'count': "36 Months*", 'text': "Warranty"}
        ],
        'saleTimerActive': True,
        'countdownEndDate': countdown_end.strftime('%Y-%m-%dT%H:%M:%S'),
        'offerText': "Visit Your Nearest Store & Get Extra UPTO",
        'discountText': "₹ 25,000 INSTANT DISCOUNT",
        'infoBadges': [
            {'icon': "Users", 'topText': "20 Lakh+", 'bottomText': "Customers"},
            {'icon': "Package", 'topText': "Free", 'bottomText': "Delivery"},
            {'icon': "CheckCircle", 'topText': "Best", 'bottomText': "Warranty*"},
            {'icon': "Building2", 'topText': "15 Lakh sq. ft.", 'bottomText': "Mfg. Unit"}
        ]
    }
    
    HomePageContent.objects.update_or_create(
        section_key='feature-card',
        defaults={
            'section_name': 'Feature Card & CTA',
            'content': feature_card_content,
            'is_active': True,
            'order': 7
        }
    )
    print("✓ Seeded Feature Card & CTA")
    
    # ==================== 8. Banner Cards ====================
    # Use first 6 products for sliders
    slider1_products = products[:6]
    slider2_products = products[:6]
    
    banner_cards_content = {
        'heading': "Crafted In India",
        'bannerCards': [
            {'img': "/images/Home/bannerCards.webp"},
            {'img': "/images/Home/bannerCards.webp"}
        ],
        'slider1Title': "Customers frequently viewed | Popular products in the last 7 days",
        'slider1ViewAllUrl': "#",
        'slider1Products': slider1_products,
        'slider2Title': "Inspired by your browsing history",
        'slider2ViewAllUrl': "#",
        'slider2Products': slider2_products
    }
    
    HomePageContent.objects.update_or_create(
        section_key='banner-cards',
        defaults={
            'section_name': 'Banner Cards',
            'content': banner_cards_content,
            'is_active': True,
            'order': 8
        }
    )
    print("✓ Seeded Banner Cards")
    
    # ==================== 9. Furniture Info Section ====================
    furniture_info_content = {
        'mainHeading': "Buy Furniture Online at Sixpine – India's One-Stop Furniture & Home Décor Destination",
        'introParagraphs': [
            "A home is where comfort lives, and furniture brings that comfort to life. Whether you're setting up a new space or giving your interiors a refreshing makeover, Sixpine offers everything you need under one roof. From elegant wooden furniture to modern décor, our collection is designed to complement every style of living.",
            "At Sixpine, we provide a vast assortment of ready-made and customizable furniture online in India. Since 2024, we've been serving customers with high-quality pieces like sofas, dining tables, wardrobes, beds, and much more—crafted from premium materials. Alongside furniture, our exclusive home décor range features wall art, planters, photo frames, tableware, glassware, and kitchen organizers. Whether you prefer minimalistic, classic, or bold designs, Sixpine makes it easy to find furniture that blends seamlessly with your lifestyle."
        ],
        'materialsSection': {
            'heading': "Discover Furniture Materials at Sixpine",
            'intro': "Every home is unique, and so are the materials that bring furniture to life. Sixpine offers furniture crafted in a variety of premium woods and materials, each with its own charm:",
            'materials': [
                {'title': "Sheesham Wood", 'description': "Rich-toned, dense, and durable, perfect for bedrooms and living rooms."},
                {'title': "Mango Wood", 'description': "Strong yet light in color, with striking natural grain patterns."},
                {'title': "Teak Wood", 'description': "Highly durable and moisture-resistant, ideal for both indoor and outdoor spaces."},
                {'title': "Engineered Wood", 'description': "Affordable, sleek, and versatile for budget-friendly home makeovers."},
                {'title': "Ash Wood", 'description': "Light-colored with a smooth finish, blending natural warmth with modern design."}
            ]
        },
        'shopByRoomSection': {
            'heading': "Shop by Room – Furniture for Every Corner of Your Home",
            'intro': "At Sixpine, we curate furniture that doesn't just serve functionality but also transforms your space into a reflection of your style.",
            'rooms': [
                {'title': "Living Room", 'description': "Sofas, recliners, center tables, lounge chairs, rocking chairs, TV units, and sofa-cum-beds."},
                {'title': "Bedroom", 'description': "Beds with storage, wardrobes, dressing tables, bunk beds, mattresses, and cushions."},
                {'title': "Dining Room", 'description': "Dining tables, chairs, crockery units, folding dining sets, and sideboards."},
                {'title': "Study Room", 'description': "Compact study tables, ergonomic chairs, foldable desks, and bookshelves."},
                {'title': "Kids' Room", 'description': "Playful and vibrant beds, wardrobes, and study tables."},
                {'title': "Office Furniture", 'description': "Ergonomic office chairs, workstations, executive tables, and office sofas."},
                {'title': "Outdoor Spaces", 'description': "Swing chairs, garden tables, planters, and pet houses."},
                {'title': "Entryway & Foyer", 'description': "Shoe racks, benches, and console tables to make the best first impression."},
                {'title': "Restaurant Furniture", 'description': "Hotel chairs, bar stools, trolleys, and tables for commercial needs."}
            ]
        },
        'exploreMoreSection': {
            'heading': "Explore More at Sixpine – Beyond Furniture",
            'intro': "Our vision is to make every home complete, which is why Sixpine also offers:",
            'items': [
                {'title': "Home Décor", 'description': "Wall mirrors, lamps, photo frames, carpets, and indoor plants to elevate your interiors."},
                {'title': "Home Furnishings", 'description': "Cushions, curtains, and premium fabrics for a cozy vibe."},
                {'title': "Lamps & Lights", 'description': "Chandeliers, table lamps, pendant lights, and designer indoor lighting."},
                {'title': "Outdoor Furniture", 'description': "Durable and stylish options for balconies, patios, and gardens."},
                {'title': "Mattresses", 'description': "High-quality latex, orthopedic, and foldable mattresses for restful sleep."},
                {'title': "Modular Kitchens", 'description': "Functional, space-saving modular designs for modern Indian homes."}
            ]
        },
        'upholsterySection': {
            'heading': "Upholstery Options at Sixpine",
            'intro': "Choosing the right fabric adds character and comfort to your furniture. At Sixpine, you'll find:",
            'options': [
                {'title': "Cotton", 'description': "Durable, eco-friendly, and easy to maintain."},
                {'title': "Velvet", 'description': "Luxurious, plush, and perfect for elegant living rooms."},
                {'title': "Leatherette", 'description': "Stylish, practical, and affordable alternative to leather."}
            ]
        },
        'buyingTipsSection': {
            'heading': "Things to Consider Before Buying Furniture Online",
            'intro': "Buying furniture online can be seamless if you keep a few things in mind:",
            'tips': [
                {'title': "Material", 'description': "Understand durability and finish."},
                {'title': "Design", 'description': "Pick what matches your décor style."},
                {'title': "Color", 'description': "Ensure it complements your interiors."},
                {'title': "Size", 'description': "Measure your space and check dimensions for easy fit."},
                {'title': "Price", 'description': "Balance between affordability and quality."},
                {'title': "Reviews", 'description': "Learn from customer experiences."},
                {'title': "Warranty", 'description': "Check coverage details."},
                {'title': "Payment Security", 'description': "Shop from a trusted platform like Sixpine."}
            ]
        },
        'careTipsSection': {
            'heading': "Furniture Care Tips",
            'tips': [
                "Dust regularly with a soft cloth or vacuum brush.",
                "Clean monthly using mild water-vinegar spray and wipe dry.",
                "Use felt pads under furniture legs to prevent scratches.",
                "Call for professional inspection for long-term maintenance."
            ]
        },
        'whyChooseSection': {
            'heading': "Why Choose Sixpine Furniture?",
            'items': [
                {'title': "Durability & Functionality", 'description': "Built for years of use."},
                {'title': "Comfort & Style", 'description': "Designed to match every lifestyle."},
                {'title': "Low Maintenance", 'description': "Easy to care for, saving long-term costs."},
                {'title': "Cost-Effective Investment", 'description': "Premium designs at fair prices."}
            ]
        },
        'experienceStoresSection': {
            'heading': "Sixpine Experience Stores – PAN India Presence",
            'intro': "Sixpine has over 100+ experience stores across India, with many more opening soon. Visit us in person to explore the diversity of our collections, or shop online for convenience. Wherever you are, Sixpine is always nearby when you search for the best furniture shop near me."
        },
        'ctaSection': {
            'heading': "Shop Affordable, Premium Furniture at Sixpine",
            'paragraphs': [
                "Buying furniture is no longer a compromise between price and quality. At Sixpine, we believe in offering both—premium designs at affordable prices. From living room to bedroom, from office to outdoors, every product is thoughtfully designed to bring joy and comfort to your home."
            ],
            'highlightText': "✨ Discover Sixpine today – where quality meets affordability, and every home finds its perfect fit."
        }
    }
    
    HomePageContent.objects.update_or_create(
        section_key='furniture-info-section',
        defaults={
            'section_name': 'Furniture Info Section',
            'content': furniture_info_content,
            'is_active': True,
            'order': 9
        }
    )
    print("✓ Seeded Furniture Info Section")
    
    print("\n" + "="*60)
    print("✅ All homepage sections seeded successfully!")
    print(f"📦 Used {len(products)} products from database for product selectors")
    print("="*60)

if __name__ == '__main__':
    seed_all_homepage_sections()

