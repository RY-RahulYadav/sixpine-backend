from django.core.management.base import BaseCommand
from products.models import Discount


class Command(BaseCommand):
    help = 'Seed predefined discount options (e.g., 10, 20, 30, 50)'

    def handle(self, *args, **options):
        self.stdout.write('Seeding discount options...')
        discounts = [10, 20, 30, 50]
        created = 0
        for pct in discounts:
            obj, was_created = Discount.objects.get_or_create(percentage=pct)
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'Created discount {pct}%'))
        self.stdout.write(self.style.SUCCESS(f'Discount seeding complete. {created} created.'))
