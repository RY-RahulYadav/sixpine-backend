from django.core.management.base import BaseCommand
from decimal import Decimal
from products.models import (
    Product, Category, Subcategory, Color, Material, ProductImage, ProductVariant,
    ProductSpecification, ProductFeature, ProductOffer, ProductRecommendation
)


class Command(BaseCommand):
    help = 'Seed sample products with variants, specifications, and features'

    def handle(self, *args, **options):
        self.stdout.write('Seeding products...')

        # Delete existing products and related data to ensure a clean seed
        self.stdout.write('Deleting existing products and related records...')
        ProductRecommendation.objects.all().delete()
        ProductOffer.objects.all().delete()
        ProductFeature.objects.all().delete()
        ProductSpecification.objects.all().delete()
        ProductVariant.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        self.stdout.write('Existing product data cleared.')
        
        # Get categories and subcategories
        sofas_category = Category.objects.get(name='Sofas')
        recliners_category = Category.objects.get(name='Recliners')
        beds_category = Category.objects.get(name='Beds')
        centre_tables_category = Category.objects.get(name='Centre Tables')
        
        three_seater = Subcategory.objects.get(name='3 Seater', category=sofas_category)
        one_seater_recliner = Subcategory.objects.get(name='1 Seater Recliners', category=recliners_category)
        king_size_beds = Subcategory.objects.get(name='King Size Beds', category=beds_category)
        coffee_tables = Subcategory.objects.get(name='Coffee Tables', category=centre_tables_category)
        
        # Get colors
        red = Color.objects.get(name='Red')
        blue = Color.objects.get(name='Blue')
        black = Color.objects.get(name='Black')
        white = Color.objects.get(name='White')
        brown = Color.objects.get(name='Brown')
    # Note: only using available colors: Red, Blue, Black, White, Brown
        
        # Get materials
        premium_fabric = Material.objects.get(name='Premium Fabric')
        premium_leather = Material.objects.get(name='Premium Leather')
        sheesham_wood = Material.objects.get(name='Sheesham Wood')
        engineered_wood = Material.objects.get(name='Engineered Wood')
        
        # Sample products data
        products_data = [
            {
                'title': 'Premium 3-Seater Sofa',
                'short_description': 'Elegant 3-seater sofa with premium upholstery and comfortable cushions.',
                'long_description': 'This premium 3-seater sofa combines style and comfort. Made with high-quality materials and featuring a modern design that complements any living room. The sofa includes comfortable cushions and durable upholstery that will last for years.',
                'category': sofas_category,
                'subcategory': three_seater,
                'price': Decimal('45000.00'),
                'old_price': Decimal('55000.00'),
                'material': premium_fabric,
                'dimensions': '220cm x 90cm x 85cm',
                'weight': '85 kg',
                'warranty': '2 years',
                'assembly_required': True,
                'is_featured': True,
                'variants': [
                    {'color': red, 'size': '3-Seater', 'pattern': 'Classic', 'stock_quantity': 10},
                    {'color': blue, 'size': '3-Seater', 'pattern': 'Modern', 'stock_quantity': 8},
                    {'color': brown, 'size': '3-Seater', 'pattern': 'Classic', 'stock_quantity': 12},
                ],
                'specifications': [
                    {'name': 'Brand', 'value': 'Sixpine'},
                    {'name': 'Style', 'value': 'Modern'},
                    {'name': 'Frame Material', 'value': 'Solid Wood'},
                    {'name': 'Upholstery', 'value': 'Premium Fabric'},
                    {'name': 'Seating Capacity', 'value': '3 People'},
                    {'name': 'Assembly', 'value': 'Required'},
                ],
                'features': [
                    'High-quality fabric upholstery',
                    'Solid wood frame for durability',
                    'Comfortable foam cushions',
                    'Easy to clean and maintain',
                    'Modern design suitable for any decor',
                    '2-year manufacturer warranty'
                ],
                'offers': [
                    {
                        'title': 'Free Delivery',
                        'description': 'Get free doorstep delivery on orders above ₹40,000',
                        'discount_percentage': None,
                        'discount_amount': None
                    },
                    {
                        'title': '10% Off on Card Payment',
                        'description': 'Get 10% additional discount when paying with XYZ credit card',
                        'discount_percentage': 10,
                        'discount_amount': None
                    }
                ]
            },
            {
                'title': 'Luxury Recliner Chair',
                'short_description': 'Premium recliner chair with massage function and USB charging port.',
                'long_description': 'Experience ultimate comfort with our luxury recliner chair. Features include massage function, USB charging port, and premium leather upholstery. Perfect for relaxation and entertainment.',
                'category': recliners_category,
                'subcategory': one_seater_recliner,
                'price': Decimal('35000.00'),
                'old_price': Decimal('42000.00'),
                'material': premium_leather,
                'dimensions': '100cm x 90cm x 110cm',
                'weight': '45 kg',
                'warranty': '3 years',
                'assembly_required': False,
                'is_featured': True,
                'variants': [
                    {'color': black, 'size': 'Standard', 'pattern': 'Classic', 'stock_quantity': 15},
                    {'color': brown, 'size': 'Standard', 'pattern': 'Classic', 'stock_quantity': 10},
                    {'color': white, 'size': 'Standard', 'pattern': 'Modern', 'stock_quantity': 8},
                ],
                'specifications': [
                    {'name': 'Brand', 'value': 'Sixpine'},
                    {'name': 'Style', 'value': 'Luxury'},
                    {'name': 'Frame Material', 'value': 'Metal'},
                    {'name': 'Upholstery', 'value': 'Premium Leather'},
                    {'name': 'Features', 'value': 'Massage, USB Charging'},
                    {'name': 'Assembly', 'value': 'Not Required'},
                ],
                'features': [
                    'Premium leather upholstery',
                    'Built-in massage function',
                    'USB charging port',
                    'Smooth reclining mechanism',
                    'Durable metal frame',
                    '3-year comprehensive warranty'
                ],
                'offers': [
                    {
                        'title': 'Free Installation',
                        'description': 'Free installation and setup service included',
                        'discount_percentage': None,
                        'discount_amount': None
                    }
                ]
            },
            {
                'title': 'King Size Bed with Storage',
                'short_description': 'Spacious king size bed with built-in storage drawers and headboard.',
                'long_description': 'This king size bed combines comfort and functionality with built-in storage drawers. Features a sturdy wooden frame, comfortable headboard, and ample storage space underneath.',
                'category': beds_category,
                'subcategory': king_size_beds,
                'price': Decimal('28000.00'),
                'old_price': Decimal('35000.00'),
                'material': sheesham_wood,
                'dimensions': '200cm x 180cm x 60cm',
                'weight': '120 kg',
                'warranty': '5 years',
                'assembly_required': True,
                'is_featured': False,
                'variants': [
                    {'color': brown, 'size': 'King Size', 'pattern': 'Classic', 'stock_quantity': 20},
                    {'color': white, 'size': 'King Size', 'pattern': 'Modern', 'stock_quantity': 15},
                    {'color': black, 'size': 'King Size', 'pattern': 'Classic', 'stock_quantity': 12},
                ],
                'specifications': [
                    {'name': 'Brand', 'value': 'Sixpine'},
                    {'name': 'Style', 'value': 'Traditional'},
                    {'name': 'Frame Material', 'value': 'Sheesham Wood'},
                    {'name': 'Storage', 'value': 'Built-in Drawers'},
                    {'name': 'Bed Size', 'value': 'King Size (6x5 ft)'},
                    {'name': 'Assembly', 'value': 'Required'},
                ],
                'features': [
                    'Solid Sheesham wood construction',
                    'Built-in storage drawers',
                    'Comfortable headboard',
                    'Durable and long-lasting',
                    'Easy to assemble',
                    '5-year warranty on frame'
                ],
                'offers': [
                    {
                        'title': 'Free Mattress',
                        'description': 'Get a free premium mattress with this bed purchase',
                        'discount_percentage': None,
                        'discount_amount': None
                    }
                ]
            },
            {
                'title': 'Modern Coffee Table',
                'short_description': 'Contemporary dining table with 6 chairs, perfect for family gatherings.',
                'long_description': 'This modern dining table set includes a spacious table and 6 comfortable chairs. Made with high-quality materials and featuring a contemporary design that enhances your dining experience.',
                'category': centre_tables_category,
                'subcategory': coffee_tables,
                'price': Decimal('25000.00'),
                'old_price': Decimal('32000.00'),
                'material': engineered_wood,
                'dimensions': '180cm x 90cm x 75cm',
                'weight': '80 kg',
                'warranty': '2 years',
                'assembly_required': True,
                'is_featured': False,
                'variants': [
                    {'color': brown, 'size': '6-Seater', 'pattern': 'Modern', 'stock_quantity': 18},
                    {'color': white, 'size': '6-Seater', 'pattern': 'Classic', 'stock_quantity': 14},
                    {'color': black, 'size': '6-Seater', 'pattern': 'Modern', 'stock_quantity': 16},
                ],
                'specifications': [
                    {'name': 'Brand', 'value': 'Sixpine'},
                    {'name': 'Style', 'value': 'Contemporary'},
                    {'name': 'Frame Material', 'value': 'Engineered Wood'},
                    {'name': 'Seating Capacity', 'value': '6 People'},
                    {'name': 'Includes', 'value': 'Table + 6 Chairs'},
                    {'name': 'Assembly', 'value': 'Required'},
                ],
                'features': [
                    'High-quality engineered wood',
                    'Comfortable padded chairs',
                    'Easy to clean surface',
                    'Sturdy construction',
                    'Modern design',
                    '2-year warranty'
                ],
                'offers': [
                    {
                        'title': 'Free Delivery & Setup',
                        'description': 'Free delivery and assembly service included',
                        'discount_percentage': None,
                        'discount_amount': None
                    }
                ]
            }
        ]
        
        # We now store image URLs directly (fields are URLField).
        # Helper to assign a remote image URL to a model field name and save the instance.
        def assign_image_url(instance, field_name, url):
            try:
                setattr(instance, field_name, url)
                instance.save()
                return True
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Failed to assign image URL {url} to {instance}: {e}'))
                return False

        # Create products
        created_products = []
        # Common image URL to use for main_image and gallery images
        common_image_url = "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8M3x8cHJvZHVjdHxlbnwwfHwwfHx8MA%3D%3D&fm=jpg&q=60&w=3000"
        for product_data in products_data:
            variants = product_data.pop('variants')
            specifications = product_data.pop('specifications')
            features = product_data.pop('features')
            offers = product_data.pop('offers')
            
            product, created = Product.objects.get_or_create(
                title=product_data['title'],
                defaults=product_data
            )
            
            if created:
                self.stdout.write(f'Created product: {product.title}')
                created_products.append(product)
                
                # Assign the common image URL as main_image (models use URLField now)
                assigned = assign_image_url(product, 'main_image', common_image_url)
                if not assigned:
                    self.stdout.write(self.style.WARNING(f'Failed to assign main_image URL for {product.title}'))

                # Create ProductImage entries and save the same downloaded image into gallery
                for idx in range(1, 4):
                    img = ProductImage.objects.create(
                        product=product,
                        alt_text=f"{product.title} image {idx}",
                        sort_order=idx,
                        image=common_image_url
                    )
                # Create variants
                for variant_data in variants:
                    ProductVariant.objects.create(
                        product=product,
                        **variant_data
                    )
                
                # Create specifications
                for spec_data in specifications:
                    ProductSpecification.objects.create(
                        product=product,
                        **spec_data
                    )
                
                # Create features
                for feature_data in features:
                    ProductFeature.objects.create(
                        product=product,
                        feature=feature_data
                    )
                
                # Create offers
                for offer_data in offers:
                    ProductOffer.objects.create(
                        product=product,
                        **offer_data
                    )
        
        # Create some recommendations between products
        if len(created_products) >= 2:
            # Sofa -> Recliner (buy with it)
            ProductRecommendation.objects.get_or_create(
                product=created_products[0],  # Sofa
                recommended_product=created_products[1],  # Recliner
                recommendation_type='buy_with',
                defaults={'sort_order': 1}
            )
            
            # Recliner -> Sofa (buy with it)
            ProductRecommendation.objects.get_or_create(
                product=created_products[1],  # Recliner
                recommended_product=created_products[0],  # Sofa
                recommendation_type='buy_with',
                defaults={'sort_order': 1}
            )
            
            # Bed -> Dining Table (inspired by)
            ProductRecommendation.objects.get_or_create(
                product=created_products[2],  # Bed
                recommended_product=created_products[3],  # Dining Table
                recommendation_type='inspired_by',
                defaults={'sort_order': 1}
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded {len(created_products)} products!')
        )