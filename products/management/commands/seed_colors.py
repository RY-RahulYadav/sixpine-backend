from django.core.management.base import BaseCommand
from products.models import Color


class Command(BaseCommand):
    help = 'Seed initial colors data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding colors...')
        
        colors_data = [
            {
                'name': 'Baby Pink',
                'hex_code': '#F4C2C2',
                'is_active': True
            },
            {
                'name': 'Beige',
                'hex_code': '#F5F5DC',
                'is_active': True
            },
            {
                'name': 'Black',
                'hex_code': '#000000',
                'is_active': True
            },
            {
                'name': 'Blue & Beige',
                'hex_code': '#0000FF',
                'is_active': True
            },
            {
                'name': 'Brown',
                'hex_code': '#8B4513',
                'is_active': True
            },
            {
                'name': 'Camel',
                'hex_code': '#C19A6B',
                'is_active': True
            },
            {
                'name': 'Cream',
                'hex_code': '#edede8',
                'is_active': True
            },
            {
                'name': 'Green',
                'hex_code': '#50C878',
                'is_active': True
            },
            {
                'name': 'Grey',
                'hex_code': '#808080',
                'is_active': True
            },
            {
                'name': 'Mustard Yellow',
                'hex_code': '#FFCE1B',
                'is_active': True
            },
            {
                'name': 'Navy Blue',
                'hex_code': '#0000FF',
                'is_active': True
            },
            {
                'name': 'Off-White (Cream)',
                'hex_code': '#FAF9F6',
                'is_active': True
            },
            {
                'name': 'Pink',
                'hex_code': '#FFC0CB',
                'is_active': True
            },
            {
                'name': 'Purple',
                'hex_code': '#A020F0',
                'is_active': True
            },
            {
                'name': 'Red',
                'hex_code': '#FF0000',
                'is_active': True
            },
            {
                'name': 'Red Wine',
                'hex_code': '#990012',
                'is_active': True
            },
            {
                'name': 'Rose Pink',
                'hex_code': '#FF66CC',
                'is_active': True
            },
            {
                'name': 'Royal Blue',
                'hex_code': '#4169E1',
                'is_active': True
            },
            {
                'name': 'Saddle',
                'hex_code': '#8B4513',
                'is_active': True
            },
            {
                'name': 'Turquoise',
                'hex_code': '#40E0D0',
                'is_active': True
            }
        ]
        
        created_count = 0
        updated_count = 0
        for color_data in colors_data:
            color, created = Color.objects.get_or_create(
                name=color_data['name'],
                defaults={
                    'hex_code': color_data['hex_code'],
                    'is_active': color_data['is_active']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created color: {color.name}')
            else:
                # Update existing color if hex_code or is_active changed
                updated = False
                if color.hex_code != color_data['hex_code']:
                    color.hex_code = color_data['hex_code']
                    updated = True
                if color.is_active != color_data['is_active']:
                    color.is_active = color_data['is_active']
                    updated = True
                if updated:
                    color.save()
                    updated_count += 1
                    self.stdout.write(f'Updated color: {color.name}')
                else:
                    self.stdout.write(f'Color already exists: {color.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded {created_count} new colors and updated {updated_count} existing colors!')
        )

