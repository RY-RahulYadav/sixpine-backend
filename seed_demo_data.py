"""
Comprehensive seed file for demo data.
This script will:
1. Delete all existing data (except superuser)
2. Populate the database with realistic sample data including:
   - Users with complete profiles
   - Categories and Brands
   - Products with multiple images, variants, attributes
   - Carts with items
   - Orders with addresses and complete order history
"""
import os
import django
import random
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.text import slugify

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from products.models import (
    Category, Brand, Product, ProductImage, ProductVariant,
    FilterAttribute, FilterAttributeOption, ProductAttribute, Review, Wishlist
)
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem, Address, OrderStatusHistory, OrderNote


class DataSeeder:
    def __init__(self):
        self.users = []
        self.categories = []
        self.brands = []
        self.products = []
        
    def clear_all_data(self):
        """Delete all existing data except superusers"""
        print("\n🗑️  Clearing existing data...")
        
        # Delete in proper order to respect foreign key constraints
        OrderNote.objects.all().delete()
        OrderStatusHistory.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Address.objects.all().delete()
        
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        
        Wishlist.objects.all().delete()
        Review.objects.all().delete()
        ProductAttribute.objects.all().delete()
        ProductVariant.objects.all().delete()
        ProductImage.objects.all().delete()
        FilterAttributeOption.objects.all().delete()
        FilterAttribute.objects.all().delete()
        Product.objects.all().delete()
        Brand.objects.all().delete()
        Category.objects.all().delete()
        
        # Delete regular users but keep superusers
        User.objects.filter(is_superuser=False).delete()
        
        print("✅ All existing data cleared!")
    
    def create_users(self):
        """Create demo users with complete profiles"""
        print("\n👥 Creating users...")
        
        users_data = [
            {
                'username': 'john_doe',
                'email': 'john.doe@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'password': 'password123',
                'profile': {
                    'phone': '+1-555-0101',
                    'date_of_birth': '1990-05-15',
                    'gender': 'M',
                    'newsletter_subscription': True,
                    'sms_notifications': True,
                    'email_notifications': True,
                }
            },
            {
                'username': 'jane_smith',
                'email': 'jane.smith@example.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'password': 'password123',
                'profile': {
                    'phone': '+1-555-0102',
                    'date_of_birth': '1992-08-22',
                    'gender': 'F',
                    'newsletter_subscription': True,
                    'sms_notifications': False,
                    'email_notifications': True,
                }
            },
            {
                'username': 'mike_wilson',
                'email': 'mike.wilson@example.com',
                'first_name': 'Mike',
                'last_name': 'Wilson',
                'password': 'password123',
                'profile': {
                    'phone': '+1-555-0103',
                    'date_of_birth': '1988-12-10',
                    'gender': 'M',
                    'newsletter_subscription': False,
                    'sms_notifications': True,
                    'email_notifications': True,
                }
            },
            {
                'username': 'sarah_jones',
                'email': 'sarah.jones@example.com',
                'first_name': 'Sarah',
                'last_name': 'Jones',
                'password': 'password123',
                'profile': {
                    'phone': '+1-555-0104',
                    'date_of_birth': '1995-03-18',
                    'gender': 'F',
                    'newsletter_subscription': True,
                    'sms_notifications': True,
                    'email_notifications': False,
                }
            },
            {
                'username': 'alex_brown',
                'email': 'alex.brown@example.com',
                'first_name': 'Alex',
                'last_name': 'Brown',
                'password': 'password123',
                'profile': {
                    'phone': '+1-555-0105',
                    'date_of_birth': '1993-07-25',
                    'gender': 'O',
                    'newsletter_subscription': True,
                    'sms_notifications': True,
                    'email_notifications': True,
                }
            },
        ]
        
        for user_data in users_data:
            profile_data = user_data.pop('profile')
            password = user_data.pop('password')
            
            user = User.objects.create_user(**user_data, password=password)
            
            # Update profile
            profile = user.profile
            profile.phone = profile_data['phone']
            profile.date_of_birth = profile_data['date_of_birth']
            profile.gender = profile_data['gender']
            profile.newsletter_subscription = profile_data['newsletter_subscription']
            profile.sms_notifications = profile_data['sms_notifications']
            profile.email_notifications = profile_data['email_notifications']
            profile.save()
            
            self.users.append(user)
            print(f"  ✓ Created user: {user.username}")
        
        print(f"✅ Created {len(self.users)} users")
    
    def create_categories(self):
        """Create product categories"""
        print("\n📁 Creating categories...")
        
        categories_data = [
            {
                'name': 'Electronics',
                'description': 'Electronic devices and gadgets',
                'parent': None,
                'subcategories': [
                    {'name': 'Smartphones', 'description': 'Mobile phones and accessories'},
                    {'name': 'Laptops', 'description': 'Laptops and notebooks'},
                    {'name': 'Tablets', 'description': 'Tablets and e-readers'},
                    {'name': 'Headphones', 'description': 'Headphones and earbuds'},
                    {'name': 'Cameras', 'description': 'Digital cameras and accessories'},
                ]
            },
            {
                'name': 'Fashion',
                'description': 'Clothing and accessories',
                'parent': None,
                'subcategories': [
                    {'name': 'Men\'s Clothing', 'description': 'Clothing for men'},
                    {'name': 'Women\'s Clothing', 'description': 'Clothing for women'},
                    {'name': 'Shoes', 'description': 'Footwear for all'},
                    {'name': 'Watches', 'description': 'Wrist watches'},
                    {'name': 'Bags', 'description': 'Bags and backpacks'},
                ]
            },
            {
                'name': 'Home & Kitchen',
                'description': 'Home appliances and kitchen items',
                'parent': None,
                'subcategories': [
                    {'name': 'Kitchen Appliances', 'description': 'Kitchen appliances and tools'},
                    {'name': 'Home Decor', 'description': 'Decorative items'},
                    {'name': 'Furniture', 'description': 'Home furniture'},
                    {'name': 'Bedding', 'description': 'Bedding and linen'},
                ]
            },
            {
                'name': 'Sports & Outdoors',
                'description': 'Sports equipment and outdoor gear',
                'parent': None,
                'subcategories': [
                    {'name': 'Fitness Equipment', 'description': 'Gym and fitness gear'},
                    {'name': 'Cycling', 'description': 'Bicycles and accessories'},
                    {'name': 'Camping', 'description': 'Camping and hiking gear'},
                ]
            },
            {
                'name': 'Books',
                'description': 'Books and magazines',
                'parent': None,
                'subcategories': [
                    {'name': 'Fiction', 'description': 'Fiction books'},
                    {'name': 'Non-Fiction', 'description': 'Non-fiction books'},
                    {'name': 'Children\'s Books', 'description': 'Books for children'},
                ]
            },
        ]
        
        for idx, cat_data in enumerate(categories_data):
            subcats = cat_data.pop('subcategories', [])
            
            category = Category.objects.create(
                name=cat_data['name'],
                slug=slugify(cat_data['name']),
                description=cat_data['description'],
                is_active=True,
                sort_order=idx
            )
            self.categories.append(category)
            print(f"  ✓ Created category: {category.name}")
            
            for sub_idx, subcat in enumerate(subcats):
                sub_category = Category.objects.create(
                    name=subcat['name'],
                    slug=slugify(subcat['name']),
                    description=subcat['description'],
                    parent=category,
                    is_active=True,
                    sort_order=sub_idx
                )
                self.categories.append(sub_category)
                print(f"    ✓ Created subcategory: {sub_category.name}")
        
        print(f"✅ Created {len(self.categories)} categories")
    
    def create_brands(self):
        """Create product brands"""
        print("\n🏷️  Creating brands...")
        
        brands_data = [
            'Apple', 'Samsung', 'Sony', 'LG', 'Dell', 'HP', 'Lenovo', 'Asus',
            'Nike', 'Adidas', 'Puma', 'Reebok', 'Levi\'s', 'H&M', 'Zara',
            'KitchenAid', 'Philips', 'Panasonic', 'Bosch', 'Cuisinart',
            'Generic', 'Premium Brand'
        ]
        
        for brand_name in brands_data:
            brand = Brand.objects.create(
                name=brand_name,
                description=f'{brand_name} - Quality products',
                is_active=True
            )
            self.brands.append(brand)
        
        print(f"✅ Created {len(self.brands)} brands")
    
    def create_products(self):
        """Create products with images, variants, and attributes"""
        print("\n📦 Creating products...")
        
        # Helper function to get category by name
        def get_category(name):
            return Category.objects.get(name=name)
        
        # Helper function to get brand by name
        def get_brand(name):
            return Brand.objects.get(name=name)
        
        products_data = [
            # Smartphones
            {
                'title': 'iPhone 15 Pro Max',
                'short_description': 'The ultimate iPhone with titanium design and A17 Pro chip',
                'description': 'iPhone 15 Pro Max features a strong and light titanium design with a textured matte glass back. It has the A17 Pro chip, a customizable Action button, and the most powerful iPhone camera system ever. USB-C connectivity. All in a phone that\'s tough to the core.',
                'category': 'Smartphones',
                'brand': 'Apple',
                'price': Decimal('1199.99'),
                'old_price': Decimal('1299.99'),
                'discount_percentage': 8,
                'stock_quantity': 50,
                'sku': 'APPL-IP15PM-001',
                'weight': Decimal('0.22'),
                'dimensions': '6.29 x 3.02 x 0.33 inches',
                'is_featured': True,
                'is_new_arrival': True,
                'images': [
                    'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQaEtVpu5NBZVyrgkDni7UlFx4HrjORx3zYyA&s',
                    'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQaEtVpu5NBZVyrgkDni7UlFx4HrjORx3zYyA&s',
                    'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQaEtVpu5NBZVyrgkDni7UlFx4HrjORx3zYyA&s',
                ],
                'variants': [
                    {'name': '256GB - Natural Titanium', 'sku': 'APPL-IP15PM-256-NT', 'price': Decimal('1199.99'), 'stock': 20, 'attrs': {'storage': '256GB', 'color': 'Natural Titanium'}},
                    {'name': '512GB - Blue Titanium', 'sku': 'APPL-IP15PM-512-BT', 'price': Decimal('1399.99'), 'stock': 15, 'attrs': {'storage': '512GB', 'color': 'Blue Titanium'}},
                    {'name': '1TB - White Titanium', 'sku': 'APPL-IP15PM-1TB-WT', 'price': Decimal('1599.99'), 'stock': 10, 'attrs': {'storage': '1TB', 'color': 'White Titanium'}},
                ],
            },
            {
                'title': 'Samsung Galaxy S24 Ultra',
                'short_description': 'Epic performance meets epic AI with Galaxy AI',
                'description': 'Meet Galaxy S24 Ultra, the ultimate form of Galaxy Ultra with a new titanium exterior and a 17.25cm (6.8") flat display. It\'s an absolute marvel of design. Enhanced with the most powerful processor yet, it blurs the lines between PC and mobile gaming, and can test your limits with Epic Ray Tracing and advanced 3D graphics.',
                'category': 'Smartphones',
                'brand': 'Samsung',
                'price': Decimal('1099.99'),
                'old_price': Decimal('1199.99'),
                'discount_percentage': 8,
                'stock_quantity': 45,
                'sku': 'SAMS-GS24U-001',
                'weight': Decimal('0.23'),
                'dimensions': '6.40 x 3.11 x 0.34 inches',
                'is_featured': True,
                'is_new_arrival': True,
                'images': [
                    'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=800',
                    'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800',
                ],
                'variants': [
                    {'name': '256GB - Titanium Gray', 'sku': 'SAMS-GS24U-256-TG', 'price': Decimal('1099.99'), 'stock': 25, 'attrs': {'storage': '256GB', 'color': 'Titanium Gray'}},
                    {'name': '512GB - Titanium Black', 'sku': 'SAMS-GS24U-512-TB', 'price': Decimal('1199.99'), 'stock': 20, 'attrs': {'storage': '512GB', 'color': 'Titanium Black'}},
                ],
            },
            # Laptops
            {
                'title': 'MacBook Pro 16" M3 Max',
                'short_description': 'Supercharged by M3 Max. Up to 18 hours of battery life.',
                'description': 'MacBook Pro blasts forward with the M3 Max chip. Built for all types of creatives, including developers, photographers, videographers, 3D artists, and more, the laptop features a brilliant Liquid Retina XDR display, wide array of connectivity ports, responsive Magic Keyboard, and six-speaker sound system.',
                'category': 'Laptops',
                'brand': 'Apple',
                'price': Decimal('2499.99'),
                'old_price': Decimal('2699.99'),
                'discount_percentage': 7,
                'stock_quantity': 30,
                'sku': 'APPL-MBP16-M3M',
                'weight': Decimal('2.15'),
                'dimensions': '14.01 x 9.77 x 0.66 inches',
                'is_featured': True,
                'is_new_arrival': True,
                'images': [
                    'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800',
                    'https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=800',
                    'https://images.unsplash.com/photo-1629131726692-1accd0c53ce0?w=800',
                ],
                'variants': [
                    {'name': '512GB SSD - Space Black', 'sku': 'APPL-MBP16-512-SB', 'price': Decimal('2499.99'), 'stock': 15, 'attrs': {'storage': '512GB SSD', 'color': 'Space Black'}},
                    {'name': '1TB SSD - Silver', 'sku': 'APPL-MBP16-1TB-SV', 'price': Decimal('2799.99'), 'stock': 15, 'attrs': {'storage': '1TB SSD', 'color': 'Silver'}},
                ],
            },
            {
                'title': 'Dell XPS 15 Laptop',
                'short_description': 'Premium performance and stunning OLED display',
                'description': 'The XPS 15 laptop delivers exceptional performance with 13th Gen Intel Core processors and NVIDIA GeForce RTX graphics. Features a stunning 15.6" OLED display with 3.5K resolution, premium materials, and all-day battery life.',
                'category': 'Laptops',
                'brand': 'Dell',
                'price': Decimal('1799.99'),
                'old_price': Decimal('1999.99'),
                'discount_percentage': 10,
                'stock_quantity': 25,
                'sku': 'DELL-XPS15-001',
                'weight': Decimal('1.86'),
                'dimensions': '13.57 x 9.06 x 0.71 inches',
                'is_featured': True,
                'is_new_arrival': False,
                'images': [
                    'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=800',
                    'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=800',
                ],
                'variants': [
                    {'name': '512GB SSD - Platinum Silver', 'sku': 'DELL-XPS15-512-PS', 'price': Decimal('1799.99'), 'stock': 15, 'attrs': {'storage': '512GB SSD', 'color': 'Platinum Silver'}},
                    {'name': '1TB SSD - Graphite', 'sku': 'DELL-XPS15-1TB-GR', 'price': Decimal('1999.99'), 'stock': 10, 'attrs': {'storage': '1TB SSD', 'color': 'Graphite'}},
                ],
            },
            # Headphones
            {
                'title': 'Sony WH-1000XM5 Wireless Headphones',
                'short_description': 'Industry-leading noise cancellation with exceptional sound quality',
                'description': 'The WH-1000XM5 headphones rewrite the rules for distraction-free listening. Two processors control 8 microphones for unprecedented noise cancellation. With a specially designed driver unit and Hi-Res audio support, immerse yourself in supreme sound quality.',
                'category': 'Headphones',
                'brand': 'Sony',
                'price': Decimal('349.99'),
                'old_price': Decimal('399.99'),
                'discount_percentage': 13,
                'stock_quantity': 60,
                'sku': 'SONY-WH1000XM5-001',
                'weight': Decimal('0.55'),
                'dimensions': '10 x 7.37 x 3.9 inches',
                'is_featured': True,
                'is_new_arrival': False,
                'images': [
                    'https://images.unsplash.com/photo-1545127398-14699f92334b?w=800',
                    'https://images.unsplash.com/photo-1484704849700-f032a568e944?w=800',
                ],
                'variants': [
                    {'name': 'Black', 'sku': 'SONY-WH1000XM5-BLK', 'price': Decimal('349.99'), 'stock': 30, 'attrs': {'color': 'Black'}},
                    {'name': 'Silver', 'sku': 'SONY-WH1000XM5-SLV', 'price': Decimal('349.99'), 'stock': 30, 'attrs': {'color': 'Silver'}},
                ],
            },
            {
                'title': 'Apple AirPods Pro (2nd Generation)',
                'short_description': 'Active Noise Cancellation and Adaptive Audio',
                'description': 'AirPods Pro feature up to 2x more Active Noise Cancellation, plus Adaptive Transparency, and Personalized Spatial Audio with dynamic head tracking for immersive sound. A single charge delivers up to 6 hours of battery life. And Touch control lets you easily adjust volume with a swipe.',
                'category': 'Headphones',
                'brand': 'Apple',
                'price': Decimal('249.99'),
                'old_price': Decimal('279.99'),
                'discount_percentage': 11,
                'stock_quantity': 80,
                'sku': 'APPL-APP2-001',
                'weight': Decimal('0.19'),
                'dimensions': '2.39 x 2.14 x 0.85 inches',
                'is_featured': True,
                'is_new_arrival': True,
                'images': [
                    'https://images.unsplash.com/photo-1606841837239-c5a1a4a07af7?w=800',
                    'https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?w=800',
                ],
                'variants': [],
            },
            # Tablets
            {
                'title': 'iPad Pro 12.9" M2',
                'short_description': 'The ultimate iPad experience with M2 chip',
                'description': 'iPad Pro features the powerful M2 chip with an 8-core CPU and 10-core GPU, making it the fastest and most advanced iPad ever. The Liquid Retina XDR display delivers extreme dynamic range with true-to-life details. Support for Apple Pencil and Magic Keyboard.',
                'category': 'Tablets',
                'brand': 'Apple',
                'price': Decimal('1099.99'),
                'old_price': Decimal('1199.99'),
                'discount_percentage': 8,
                'stock_quantity': 40,
                'sku': 'APPL-IPADPM2-001',
                'weight': Decimal('1.50'),
                'dimensions': '11.04 x 8.46 x 0.25 inches',
                'is_featured': True,
                'is_new_arrival': False,
                'images': [
                    'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=800',
                    'https://images.unsplash.com/photo-1585790050230-5dd28404f865?w=800',
                ],
                'variants': [
                    {'name': '128GB - Space Gray', 'sku': 'APPL-IPADPM2-128-SG', 'price': Decimal('1099.99'), 'stock': 20, 'attrs': {'storage': '128GB', 'color': 'Space Gray'}},
                    {'name': '256GB - Silver', 'sku': 'APPL-IPADPM2-256-SV', 'price': Decimal('1199.99'), 'stock': 20, 'attrs': {'storage': '256GB', 'color': 'Silver'}},
                ],
            },
            # Cameras
            {
                'title': 'Sony Alpha a7 IV Mirrorless Camera',
                'short_description': 'Full-frame mirrorless camera with 33MP and advanced AF',
                'description': 'The α7 IV is a sophisticated hybrid camera designed for photographers and videographers. It features a 33MP full-frame sensor, Real-time Eye AF for human and animal subjects, 10 fps continuous shooting, and 4K 60p video recording.',
                'category': 'Cameras',
                'brand': 'Sony',
                'price': Decimal('2499.99'),
                'old_price': Decimal('2799.99'),
                'discount_percentage': 11,
                'stock_quantity': 20,
                'sku': 'SONY-A7IV-001',
                'weight': Decimal('1.43'),
                'dimensions': '5.13 x 3.82 x 3.07 inches',
                'is_featured': True,
                'is_new_arrival': False,
                'images': [
                    'https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=800',
                    'https://images.unsplash.com/photo-1606933248010-80b76ce3e511?w=800',
                ],
                'variants': [],
            },
            # Fashion - Men's Clothing
            {
                'title': 'Nike Dri-FIT Training T-Shirt',
                'short_description': 'Moisture-wicking performance tee for workouts',
                'description': 'The Nike Dri-FIT Training T-Shirt is made with sweat-wicking fabric to help you stay dry and comfortable during your workout. The relaxed fit gives you plenty of room to move while the soft, stretchy fabric provides all-day comfort.',
                'category': 'Men\'s Clothing',
                'brand': 'Nike',
                'price': Decimal('29.99'),
                'old_price': Decimal('39.99'),
                'discount_percentage': 25,
                'stock_quantity': 100,
                'sku': 'NIKE-DRFIT-TS-001',
                'weight': Decimal('0.20'),
                'dimensions': 'Standard fit',
                'is_featured': False,
                'is_new_arrival': True,
                'images': [
                    'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800',
                    'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=800',
                ],
                'variants': [
                    {'name': 'Small - Black', 'sku': 'NIKE-DRFIT-S-BLK', 'price': Decimal('29.99'), 'stock': 25, 'attrs': {'size': 'S', 'color': 'Black'}},
                    {'name': 'Medium - Black', 'sku': 'NIKE-DRFIT-M-BLK', 'price': Decimal('29.99'), 'stock': 30, 'attrs': {'size': 'M', 'color': 'Black'}},
                    {'name': 'Large - Navy', 'sku': 'NIKE-DRFIT-L-NAV', 'price': Decimal('29.99'), 'stock': 25, 'attrs': {'size': 'L', 'color': 'Navy'}},
                    {'name': 'X-Large - Gray', 'sku': 'NIKE-DRFIT-XL-GRY', 'price': Decimal('29.99'), 'stock': 20, 'attrs': {'size': 'XL', 'color': 'Gray'}},
                ],
            },
            {
                'title': 'Levi\'s 501 Original Jeans',
                'short_description': 'Classic straight fit jeans with iconic style',
                'description': 'The Levi\'s 501 Original is the original blue jean. These jeans have been worn by miners, rebels, rock stars, and fashion icons. They feature a classic straight fit from hip to ankle, button fly, and the iconic stitching you know and love.',
                'category': 'Men\'s Clothing',
                'brand': 'Levi\'s',
                'price': Decimal('69.99'),
                'old_price': Decimal('89.99'),
                'discount_percentage': 22,
                'stock_quantity': 80,
                'sku': 'LEVI-501-001',
                'weight': Decimal('0.60'),
                'dimensions': 'Straight fit',
                'is_featured': False,
                'is_new_arrival': False,
                'images': [
                    'https://images.unsplash.com/photo-1542272604-787c3835535d?w=800',
                    'https://images.unsplash.com/photo-1604176354204-9268737828e4?w=800',
                ],
                'variants': [
                    {'name': '30x32 - Medium Blue', 'sku': 'LEVI-501-3032-MBL', 'price': Decimal('69.99'), 'stock': 20, 'attrs': {'waist': '30', 'length': '32', 'color': 'Medium Blue'}},
                    {'name': '32x32 - Medium Blue', 'sku': 'LEVI-501-3232-MBL', 'price': Decimal('69.99'), 'stock': 25, 'attrs': {'waist': '32', 'length': '32', 'color': 'Medium Blue'}},
                    {'name': '34x32 - Dark Blue', 'sku': 'LEVI-501-3432-DBL', 'price': Decimal('69.99'), 'stock': 20, 'attrs': {'waist': '34', 'length': '32', 'color': 'Dark Blue'}},
                    {'name': '36x32 - Black', 'sku': 'LEVI-501-3632-BLK', 'price': Decimal('69.99'), 'stock': 15, 'attrs': {'waist': '36', 'length': '32', 'color': 'Black'}},
                ],
            },
            # Shoes
            {
                'title': 'Nike Air Max 270',
                'short_description': 'Max Air unit delivers bold style and unbelievable comfort',
                'description': 'Nike\'s first lifestyle Air Max brings you style, comfort and big attitude in the Nike Air Max 270. The design draws inspiration from Air Max icons, showcasing Nike\'s greatest innovation with its large window and fresh array of colors.',
                'category': 'Shoes',
                'brand': 'Nike',
                'price': Decimal('149.99'),
                'old_price': Decimal('179.99'),
                'discount_percentage': 17,
                'stock_quantity': 70,
                'sku': 'NIKE-AM270-001',
                'weight': Decimal('0.80'),
                'dimensions': 'Standard fit',
                'is_featured': True,
                'is_new_arrival': False,
                'images': [
                    'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800',
                    'https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=800',
                ],
                'variants': [
                    {'name': 'US 8 - Black/White', 'sku': 'NIKE-AM270-8-BW', 'price': Decimal('149.99'), 'stock': 15, 'attrs': {'size': 'US 8', 'color': 'Black/White'}},
                    {'name': 'US 9 - Black/White', 'sku': 'NIKE-AM270-9-BW', 'price': Decimal('149.99'), 'stock': 20, 'attrs': {'size': 'US 9', 'color': 'Black/White'}},
                    {'name': 'US 10 - Triple Black', 'sku': 'NIKE-AM270-10-TB', 'price': Decimal('149.99'), 'stock': 20, 'attrs': {'size': 'US 10', 'color': 'Triple Black'}},
                    {'name': 'US 11 - White/Red', 'sku': 'NIKE-AM270-11-WR', 'price': Decimal('149.99'), 'stock': 15, 'attrs': {'size': 'US 11', 'color': 'White/Red'}},
                ],
            },
            {
                'title': 'Adidas Ultraboost 22',
                'short_description': 'Energy-returning running shoes with responsive cushioning',
                'description': 'The Ultraboost 22 running shoes are made in part with Primeblue, a high-performance recycled material featuring Parley Ocean Plastic. The adaptive Primeknit+ upper delivers a snug, supportive fit and Boost cushioning provides unbelievable energy return.',
                'category': 'Shoes',
                'brand': 'Adidas',
                'price': Decimal('189.99'),
                'old_price': Decimal('219.99'),
                'discount_percentage': 14,
                'stock_quantity': 60,
                'sku': 'ADID-UB22-001',
                'weight': Decimal('0.75'),
                'dimensions': 'Standard fit',
                'is_featured': True,
                'is_new_arrival': True,
                'images': [
                    'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=800',
                    'https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=800',
                ],
                'variants': [
                    {'name': 'US 8 - Core Black', 'sku': 'ADID-UB22-8-CB', 'price': Decimal('189.99'), 'stock': 15, 'attrs': {'size': 'US 8', 'color': 'Core Black'}},
                    {'name': 'US 9 - Cloud White', 'sku': 'ADID-UB22-9-CW', 'price': Decimal('189.99'), 'stock': 20, 'attrs': {'size': 'US 9', 'color': 'Cloud White'}},
                    {'name': 'US 10 - Solar Red', 'sku': 'ADID-UB22-10-SR', 'price': Decimal('189.99'), 'stock': 15, 'attrs': {'size': 'US 10', 'color': 'Solar Red'}},
                    {'name': 'US 11 - Core Black', 'sku': 'ADID-UB22-11-CB', 'price': Decimal('189.99'), 'stock': 10, 'attrs': {'size': 'US 11', 'color': 'Core Black'}},
                ],
            },
            # Watches
            {
                'title': 'Apple Watch Series 9 GPS',
                'short_description': 'The most powerful Apple Watch with advanced health features',
                'description': 'Apple Watch Series 9 features the new S9 chip for faster performance and on-device Siri. The bright Always-On Retina display, advanced health sensors including blood oxygen and ECG, and comprehensive fitness tracking make it the ultimate health and fitness companion.',
                'category': 'Watches',
                'brand': 'Apple',
                'price': Decimal('399.99'),
                'old_price': Decimal('429.99'),
                'discount_percentage': 7,
                'stock_quantity': 50,
                'sku': 'APPL-AWS9-001',
                'weight': Decimal('0.07'),
                'dimensions': '1.73 x 1.50 x 0.41 inches',
                'is_featured': True,
                'is_new_arrival': True,
                'images': [
                    'https://images.unsplash.com/photo-1434494878577-86c23bcb06b9?w=800',
                    'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=800',
                ],
                'variants': [
                    {'name': '41mm - Midnight Aluminum', 'sku': 'APPL-AWS9-41-MA', 'price': Decimal('399.99'), 'stock': 25, 'attrs': {'size': '41mm', 'color': 'Midnight Aluminum'}},
                    {'name': '45mm - Starlight Aluminum', 'sku': 'APPL-AWS9-45-SA', 'price': Decimal('429.99'), 'stock': 25, 'attrs': {'size': '45mm', 'color': 'Starlight Aluminum'}},
                ],
            },
            # Home & Kitchen
            {
                'title': 'KitchenAid Artisan Stand Mixer',
                'short_description': '5-quart tilt-head stand mixer with 10 speeds',
                'description': 'The KitchenAid Artisan Series 5-Qt. Tilt-Head Stand Mixer features a tilt-head design that allows clear access to the bowl for easy addition of ingredients. The mixer includes a coated flat beater, coated dough hook, 6-wire whip and pouring shield.',
                'category': 'Kitchen Appliances',
                'brand': 'KitchenAid',
                'price': Decimal('349.99'),
                'old_price': Decimal('429.99'),
                'discount_percentage': 19,
                'stock_quantity': 35,
                'sku': 'KAID-ASM-001',
                'weight': Decimal('22.00'),
                'dimensions': '14.1 x 8.7 x 14 inches',
                'is_featured': True,
                'is_new_arrival': False,
                'images': [
                    'https://images.unsplash.com/photo-1570222094114-d054a817e56b?w=800',
                    'https://images.unsplash.com/photo-1556910633-5099dc3971e8?w=800',
                ],
                'variants': [
                    {'name': 'Empire Red', 'sku': 'KAID-ASM-ER', 'price': Decimal('349.99'), 'stock': 15, 'attrs': {'color': 'Empire Red'}},
                    {'name': 'Onyx Black', 'sku': 'KAID-ASM-OB', 'price': Decimal('349.99'), 'stock': 10, 'attrs': {'color': 'Onyx Black'}},
                    {'name': 'Silver', 'sku': 'KAID-ASM-SV', 'price': Decimal('349.99'), 'stock': 10, 'attrs': {'color': 'Silver'}},
                ],
            },
            {
                'title': 'Philips Air Fryer XXL',
                'short_description': 'Extra large capacity air fryer with rapid air technology',
                'description': 'The Philips Premium Airfryer XXL is the only airfryer with Fat Removal Technology that removes and captures excess fat. Rapid Air Technology circulates hot air to fry your favorites with up to 90% less fat. Extra-large capacity fits a whole chicken.',
                'category': 'Kitchen Appliances',
                'brand': 'Philips',
                'price': Decimal('299.99'),
                'old_price': Decimal('349.99'),
                'discount_percentage': 14,
                'stock_quantity': 40,
                'sku': 'PHIL-AFXXL-001',
                'weight': Decimal('17.00'),
                'dimensions': '12.4 x 17.5 x 11.9 inches',
                'is_featured': False,
                'is_new_arrival': True,
                'images': [
                    'https://images.unsplash.com/photo-1585515320310-259814833e62?w=800',
                    'https://images.unsplash.com/photo-1595273670150-bd0c3c392e46?w=800',
                ],
                'variants': [],
            },
            # Sports & Outdoors
            {
                'title': 'Bowflex SelectTech 552 Dumbbells',
                'short_description': 'Adjustable dumbbells that replace 15 sets of weights',
                'description': 'With just the turn of a dial, change your resistance from 5 lbs all the way up to 52.5 lbs of weight. This unique design saves space and is perfect for those who want a variety of weight options without cluttering their workout area with dumbbells.',
                'category': 'Fitness Equipment',
                'brand': 'Generic',
                'price': Decimal('349.99'),
                'old_price': Decimal('429.99'),
                'discount_percentage': 19,
                'stock_quantity': 25,
                'sku': 'BWFX-ST552-001',
                'weight': Decimal('52.50'),
                'dimensions': '15.75 x 8 x 9 inches',
                'is_featured': True,
                'is_new_arrival': False,
                'images': [
                    'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=800',
                    'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800',
                ],
                'variants': [],
            },
            # Books
            {
                'title': 'Atomic Habits by James Clear',
                'short_description': 'An Easy & Proven Way to Build Good Habits & Break Bad Ones',
                'description': 'No matter your goals, Atomic Habits offers a proven framework for improving every day. James Clear reveals practical strategies that will teach you exactly how to form good habits, break bad ones, and master the tiny behaviors that lead to remarkable results.',
                'category': 'Non-Fiction',
                'brand': 'Generic',
                'price': Decimal('16.99'),
                'old_price': Decimal('19.99'),
                'discount_percentage': 15,
                'stock_quantity': 150,
                'sku': 'BOOK-AH-001',
                'weight': Decimal('0.65'),
                'dimensions': '8.25 x 5.5 x 1 inches',
                'is_featured': True,
                'is_new_arrival': False,
                'images': [
                    'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=800',
                    'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=800',
                ],
                'variants': [],
            },
        ]
        
        for product_data in products_data:
            # Get category and brand
            category = get_category(product_data['category'])
            brand = get_brand(product_data['brand']) if product_data.get('brand') else None
            
            # Extract images and variants
            images = product_data.pop('images', [])
            variants_data = product_data.pop('variants', [])
            
            # Create product
            product = Product.objects.create(
                title=product_data['title'],
                short_description=product_data['short_description'],
                description=product_data['description'],
                category=category,
                brand=brand,
                price=product_data['price'],
                old_price=product_data.get('old_price'),
                discount_percentage=product_data.get('discount_percentage', 0),
                stock_quantity=product_data['stock_quantity'],
                sku=product_data['sku'],
                weight=product_data.get('weight'),
                dimensions=product_data.get('dimensions', ''),
                slug=slugify(product_data['title']),
                meta_title=product_data['title'],
                meta_description=product_data['short_description'],
                is_active=True,
                is_featured=product_data.get('is_featured', False),
                is_new_arrival=product_data.get('is_new_arrival', False),
                availability='in_stock' if product_data['stock_quantity'] > 10 else 'limited_stock',
            )
            
            # Create product images
            for idx, image_url in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image=image_url,
                    alt_text=f'{product.title} - Image {idx + 1}',
                    is_main=(idx == 0),
                    order=idx
                )
            
            # Create product variants
            for variant_data in variants_data:
                ProductVariant.objects.create(
                    product=product,
                    sku=variant_data['sku'],
                    name=variant_data['name'],
                    price=variant_data.get('price'),
                    stock_quantity=variant_data['stock'],
                    attributes=variant_data['attrs'],
                    is_active=True
                )
            
            self.products.append(product)
            print(f"  ✓ Created product: {product.title} ({len(images)} images, {len(variants_data)} variants)")
        
        print(f"✅ Created {len(self.products)} products")
    
    def create_reviews(self):
        """Create product reviews"""
        print("\n⭐ Creating product reviews...")
        
        reviews_count = 0
        review_templates = [
            {
                'rating': 5,
                'title': 'Excellent product!',
                'comment': 'This product exceeded my expectations. The quality is outstanding and it works perfectly. Highly recommend!',
            },
            {
                'rating': 5,
                'title': 'Best purchase ever!',
                'comment': 'I absolutely love this! Great quality, fast shipping, and exactly as described. Will buy again.',
            },
            {
                'rating': 4,
                'title': 'Very good, with minor issues',
                'comment': 'Overall a great product. Does what it\'s supposed to do. Only minor complaint is the packaging could be better.',
            },
            {
                'rating': 4,
                'title': 'Good value for money',
                'comment': 'Quality is good considering the price. Would recommend to friends and family.',
            },
            {
                'rating': 5,
                'title': 'Perfect!',
                'comment': 'Everything about this product is perfect. From the design to the functionality. Five stars!',
            },
            {
                'rating': 3,
                'title': 'It\'s okay',
                'comment': 'Product is decent but nothing special. Does the job but I expected a bit more quality.',
            },
        ]
        
        # Create reviews for featured products
        for product in self.products[:10]:  # Review first 10 products
            num_reviews = random.randint(2, 4)
            selected_users = random.sample(self.users, min(num_reviews, len(self.users)))
            
            for user in selected_users:
                template = random.choice(review_templates)
                Review.objects.create(
                    product=product,
                    user=user,
                    rating=template['rating'],
                    title=template['title'],
                    comment=template['comment'],
                    is_approved=True,
                    is_verified_purchase=random.choice([True, False]),
                    helpful_votes=random.randint(0, 20)
                )
                reviews_count += 1
        
        print(f"✅ Created {reviews_count} reviews")
    
    def create_addresses(self):
        """Create addresses for users"""
        print("\n🏠 Creating addresses...")
        
        addresses_data = [
            {
                'type': 'home',
                'full_name': 'John Doe',
                'phone': '+1-555-0101',
                'street_address': '123 Main Street, Apt 4B',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10001',
                'country': 'USA',
                'is_default': True,
            },
            {
                'type': 'work',
                'full_name': 'John Doe',
                'phone': '+1-555-0101',
                'street_address': '456 Business Ave, Suite 200',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10002',
                'country': 'USA',
                'is_default': False,
            },
        ]
        
        total_addresses = 0
        for user in self.users:
            for addr_data in addresses_data:
                # Personalize address
                personalized_addr = addr_data.copy()
                personalized_addr['full_name'] = user.get_full_name() or user.username
                personalized_addr['phone'] = user.profile.phone or '+1-555-0000'
                
                Address.objects.create(user=user, **personalized_addr)
                total_addresses += 1
        
        print(f"✅ Created {total_addresses} addresses")
    
    def create_carts(self):
        """Create shopping carts with items"""
        print("\n🛒 Creating shopping carts...")
        
        carts_created = 0
        items_created = 0
        
        for user in self.users[:3]:  # First 3 users have active carts
            cart = Cart.objects.create(user=user)
            carts_created += 1
            
            # Add random products to cart
            num_items = random.randint(2, 5)
            selected_products = random.sample(self.products, min(num_items, len(self.products)))
            
            for product in selected_products:
                quantity = random.randint(1, 3)
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=quantity
                )
                items_created += 1
        
        print(f"✅ Created {carts_created} carts with {items_created} items")
    
    def create_orders(self):
        """Create orders with complete information"""
        print("\n📦 Creating orders...")
        
        order_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered']
        payment_statuses = ['paid', 'pending']
        
        orders_created = 0
        order_items_created = 0
        
        for user in self.users:
            # Create 2-4 orders per user
            num_orders = random.randint(2, 4)
            user_addresses = Address.objects.filter(user=user)
            
            if not user_addresses.exists():
                continue
            
            for _ in range(num_orders):
                # Select random products for order with their quantities
                num_items = random.randint(1, 4)
                selected_products = random.sample(self.products, min(num_items, len(self.products)))
                
                # Build items list with quantities
                items_with_quantities = []
                for product in selected_products:
                    quantity = random.randint(1, 2)
                    items_with_quantities.append((product, quantity))
                
                # Calculate order totals CORRECTLY
                subtotal = Decimal('0.00')
                for product, quantity in items_with_quantities:
                    subtotal += product.price * Decimal(str(quantity))
                
                # Apply shipping and tax
                shipping_cost = Decimal('10.00') if subtotal < Decimal('500.00') else Decimal('0.00')
                tax_amount = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))  # 5% tax, rounded
                total_amount = (subtotal + shipping_cost + tax_amount).quantize(Decimal('0.01'))
                

                # Create order with varying statuses
                
                status = random.choice(order_statuses)
                payment_status = 'paid' if status in ['delivered', 'shipped', 'processing'] else random.choice(payment_statuses)
                
                # Calculate delivery date
                created_date = timezone.now() - timedelta(days=random.randint(1, 60))
                estimated_delivery = created_date + timedelta(days=random.randint(3, 10))
                delivered_at = created_date + timedelta(days=random.randint(5, 12)) if status == 'delivered' else None
                
                # Create order with calculated totals
                order = Order.objects.create(
                    user=user,
                    status=status,
                    payment_status=payment_status,
                    subtotal=subtotal,
                    shipping_cost=shipping_cost,
                    tax_amount=tax_amount,
                    total_amount=total_amount,
                    shipping_address=random.choice(user_addresses),
                    tracking_number=f'TRK{random.randint(100000, 999999)}' if status in ['shipped', 'delivered'] else '',
                    estimated_delivery=estimated_delivery,
                    delivered_at=delivered_at,
                    order_notes=f'Order placed by {user.get_full_name() or user.username}',
                    created_at=created_date,
                )
                orders_created += 1
                
                # Create order items using the same quantities calculated earlier
                for product, quantity in items_with_quantities:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=product.price  # Price at time of order
                    )
                    order_items_created += 1
                
                # Create order status history
                OrderStatusHistory.objects.create(
                    order=order,
                    status='pending',
                    notes='Order created',
                    created_at=created_date,
                    created_by=user
                )
                
                if status in ['confirmed', 'processing', 'shipped', 'delivered']:
                    OrderStatusHistory.objects.create(
                        order=order,
                        status='confirmed',
                        notes='Order confirmed',
                        created_at=created_date + timedelta(hours=2),
                        created_by=user
                    )
                
                if status in ['processing', 'shipped', 'delivered']:
                    OrderStatusHistory.objects.create(
                        order=order,
                        status='processing',
                        notes='Order is being processed',
                        created_at=created_date + timedelta(days=1),
                        created_by=user
                    )
                
                if status in ['shipped', 'delivered']:
                    OrderStatusHistory.objects.create(
                        order=order,
                        status='shipped',
                        notes=f'Order shipped with tracking number {order.tracking_number}',
                        created_at=created_date + timedelta(days=2),
                        created_by=user
                    )
                
                if status == 'delivered':
                    OrderStatusHistory.objects.create(
                        order=order,
                        status='delivered',
                        notes='Order delivered successfully',
                        created_at=delivered_at,
                        created_by=user
                    )
                
                # Add order notes
                if random.choice([True, False]):
                    OrderNote.objects.create(
                        order=order,
                        content=random.choice([
                            'Please deliver before 5 PM',
                            'Leave at front door if not home',
                            'Call before delivery',
                            'Handle with care - fragile items'
                        ]),
                        created_at=created_date,
                        created_by=user
                    )
        
        print(f"✅ Created {orders_created} orders with {order_items_created} items")
    
    def create_wishlists(self):
        """Create wishlist items for users"""
        print("\n💝 Creating wishlists...")
        
        wishlist_items = 0
        
        for user in self.users:
            # Add 3-6 products to wishlist
            num_items = random.randint(3, 6)
            selected_products = random.sample(self.products, min(num_items, len(self.products)))
            
            for product in selected_products:
                Wishlist.objects.create(user=user, product=product)
                wishlist_items += 1
        
        print(f"✅ Created {wishlist_items} wishlist items")
    
    def run(self):
        """Run the complete seeding process"""
        print("=" * 60)
        print("🌱 STARTING DATABASE SEEDING")
        print("=" * 60)
        
        start_time = timezone.now()
        
        self.clear_all_data()
        self.create_users()
        self.create_categories()
        self.create_brands()
        self.create_products()
        self.create_reviews()
        self.create_addresses()
        self.create_carts()
        self.create_orders()
        self.create_wishlists()
        
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"⏱️  Time taken: {duration:.2f} seconds")
        print("\n📊 Summary:")
        print(f"   - Users: {len(self.users)}")
        print(f"   - Categories: {len(self.categories)}")
        print(f"   - Brands: {len(self.brands)}")
        print(f"   - Products: {len(self.products)}")
        print(f"   - Reviews: {Review.objects.count()}")
        print(f"   - Addresses: {Address.objects.count()}")
        print(f"   - Carts: {Cart.objects.count()}")
        print(f"   - Cart Items: {CartItem.objects.count()}")
        print(f"   - Orders: {Order.objects.count()}")
        print(f"   - Order Items: {OrderItem.objects.count()}")
        print(f"   - Wishlist Items: {Wishlist.objects.count()}")
        print("=" * 60)
        print("\n💡 You can now:")
        print("   1. Login with any user (username: john_doe, password: password123)")
        print("   2. Browse products with images and variants")
        print("   3. View orders and order history")
        print("   4. Access admin panel (if superuser exists)")
        print("=" * 60)


if __name__ == "__main__":
    seeder = DataSeeder()
    seeder.run()
