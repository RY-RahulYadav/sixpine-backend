from django.core.management.base import BaseCommand
from orders.models import Order
from django.db import transaction


class Command(BaseCommand):
    help = 'Delete all orders from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=int,
            help='Delete orders for a specific user ID only',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without prompt',
        )

    def handle(self, *args, **options):
        user_id = options.get('user')
        confirm = options.get('confirm', False)

        if user_id:
            orders = Order.objects.filter(user_id=user_id)
            count = orders.count()
            if count == 0:
                self.stdout.write(self.style.WARNING(f'No orders found for user ID {user_id}'))
                return
        else:
            orders = Order.objects.all()
            count = orders.count()
            if count == 0:
                self.stdout.write(self.style.WARNING('No orders found in database'))
                return

        if not confirm:
            confirm_msg = f'Are you sure you want to delete {count} order(s)? (yes/no): '
            response = input(confirm_msg)
            if response.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Deletion cancelled'))
                return

        try:
            with transaction.atomic():
                deleted_count, _ = orders.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully deleted {deleted_count} order(s)')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error deleting orders: {str(e)}')
            )

