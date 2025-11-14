from django.core.management.base import BaseCommand
from products.models import Product, ProductOffer
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seed sample offers for products'

    def handle(self, *args, **options):
        self.stdout.write('Seeding product offers...')

        # Delete existing offers
        ProductOffer.objects.all().delete()
        self.stdout.write('Existing offers cleared.')

        # Get some products
        products = Product.objects.filter(is_active=True)[:10]

        if not products.exists():
            self.stdout.write(
                self.style.WARNING('No products found. Please seed products first.')
            )
            return

        # Get current time
        now = timezone.now()

        # Sample offers data
        offers_data = [
            {
                'title': 'Special Offer: 20% Off',
                'description': 'Get amazing 20% off on this premium product! Limited time offer.',
                'discount_percentage': 20,
                'discount_amount': None,
                'is_active': True,
                'valid_from': now,
                'valid_until': now + timedelta(days=30)
            },
            {
                'title': 'Flash Sale: 30% Off',
                'description': 'Don\'t miss out on this exclusive flash sale! 30% off for today only.',
                'discount_percentage': 30,
                'discount_amount': None,
                'is_active': True,
                'valid_from': now,
                'valid_until': now + timedelta(days=7)
            },
            {
                'title': 'Limited Time: 25% Off',
                'description': 'Special offer for a limited time. Get 25% off on your favorite product!',
                'discount_percentage': 25,
                'discount_amount': None,
                'is_active': True,
                'valid_from': now,
                'valid_until': now + timedelta(days=15)
            },
            {
                'title': 'Weekend Special: 15% Off',
                'description': 'Weekend special offer! Enjoy 15% off on all products this weekend.',
                'discount_percentage': 15,
                'discount_amount': None,
                'is_active': True,
                'valid_from': now,
                'valid_until': now + timedelta(days=2)
            },
            {
                'title': 'Buy Now Save More',
                'description': 'Special discount for early birds! Save more when you buy now.',
                'discount_percentage': 18,
                'discount_amount': None,
                'is_active': True,
                'valid_from': now,
                'valid_until': now + timedelta(days=10)
            }
        ]

        created_count = 0

        # Create offers for products
        for i, product in enumerate(products):
            if i < len(offers_data):
                offer_data = offers_data[i]
                ProductOffer.objects.create(
                    product=product,
                    **offer_data
                )
                created_count += 1
                self.stdout.write(f'Created offer "{offer_data["title"]}" for product: {product.title}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded {created_count} offers!')
        )

