from django.core.management.base import BaseCommand
from products.models import Material


class Command(BaseCommand):
    help = 'Seed initial materials data'
    Material.objects.all().delete()
    def handle(self, *args, **options):
        self.stdout.write('Seeding materials...')
        
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
                self.stdout.write(f'Created material: {material.name}')
            else:
                self.stdout.write(f'Material already exists: {material.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded {created_count} materials!')
        )
