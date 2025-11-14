from django.core.management.base import BaseCommand
from products.models import Category, Subcategory, Color


class Command(BaseCommand):
    help = 'Seed categories, subcategories, and colors'

    def handle(self, *args, **options):
        self.stdout.write('Seeding categories, subcategories, and colors...')
        Category.objects.all().delete()
        Subcategory.objects.all().delete()
        Color.objects.all().delete()
        # Create colors (5-6 colors for default filter options)
        colors_data = [
            {'name': 'Red', 'hex_code': '#FF0000'},
            {'name': 'Blue', 'hex_code': '#0000FF'},
            {'name': 'Black', 'hex_code': '#000000'},
            {'name': 'White', 'hex_code': '#FFFFFF'},
            {'name': 'Brown', 'hex_code': '#8B4513'},
            {'name': 'Grey', 'hex_code': '#808080'},
        ]
        
        for color_data in colors_data:
            color, created = Color.objects.get_or_create(
                name=color_data['name'],
                defaults={'hex_code': color_data['hex_code']}
            )
            if created:
                self.stdout.write(f'Created color: {color.name}')
        
        # Create categories and subcategories based on the image
        categories_data = [
            {
                'name': 'Sofas',
                'subcategories': [
                    '3 Seater',
                    '2 Seater',
                    '1 Seater',
                    'Sofa Sets'
                ]
            },
            {
                'name': 'Recliners',
                'subcategories': [
                    '1 Seater Recliners',
                    '2 Seater Recliners',
                    '3 Seater Recliners',
                    'Recliners Sets'
                ]
            },
            {
                'name': 'Rocking Chairs',
                'subcategories': [
                    'Modern',
                    'Relax in Motion',
                    'Classic'
                ]
            },
            {
                'name': 'Beds',
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
                'subcategories': [
                    'Coffee Tables',
                    'Coffee Tables Set'
                ]
            },
            {
                'name': 'Sectional Sofas',
                'subcategories': [
                    'LHS Sectionals',
                    'RHS Sectionals',
                    'Corner Sofas'
                ]
            },
            {
                'name': 'Chaise Loungers',
                'subcategories': [
                    '3 Seater Chaise Loungers',
                    '2 Seater Chaise Loungers'
                ]
            },
            {
                'name': 'Chairs',
                'subcategories': [
                    'Arm Chairs',
                    'Accent Chairs'
                ]
            },
            {
                'name': 'Sofa Cum Beds',
                'subcategories': [
                    'Pull Out Type',
                    'Convertible Type'
                ]
            },
            {
                'name': 'Shoe Racks',
                'subcategories': [
                    'Shoe Cabinets',
                    'Shoe Racks'
                ]
            },
            {
                'name': 'Settees & Benches',
                'subcategories': [
                    'Settees',
                    'Benches'
                ]
            },
            {
                'name': 'Ottomans',
                'subcategories': [
                    'Ottomans with Storage',
                    'Decorative Ottomans'
                ]
            },
            {
                'name': 'Sofa Chairs',
                'subcategories': [
                    'Lounge Chairs',
                    'Wing Chairs'
                ]
            },
            {
                'name': 'Stool & Pouffes',
                'subcategories': [
                    'Foot Stools',
                    'Seating Stools',
                    'Pouffes'
                ]
            }
        ]
        
        for category_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={'description': f'Furniture for {category_data["name"].lower()}'}
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
            
            # Create subcategories
            for subcategory_name in category_data['subcategories']:
                subcategory, created = Subcategory.objects.get_or_create(
                    name=subcategory_name,
                    category=category,
                    defaults={'description': f'{subcategory_name} for {category.name.lower()}'}
                )
                if created:
                    self.stdout.write(f'Created subcategory: {category.name} - {subcategory.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded categories, subcategories, and colors!')
        )