from django.core.management.base import BaseCommand
from accounts.models import User, PaymentPreference
from orders.models import Address


class Command(BaseCommand):
    help = 'Seed test users for Razorpay testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of test users to create (default: 3)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test users before creating new ones'
        )

    def handle(self, *args, **options):
        count = options['count']
        clear_existing = options['clear']

        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('🌱 Seeding Test Users'))
        self.stdout.write('=' * 60)

        # Clear existing test users if requested
        if clear_existing:
            self.stdout.write('\n🗑️  Clearing existing test users...')
            test_users = User.objects.filter(email__startswith='testuser')
            deleted_count = test_users.count()
            test_users.delete()
            self.stdout.write(self.style.SUCCESS(f'✅ Deleted {deleted_count} existing test users'))

        # Test user data
        test_users_data = [
            {
                'username': 'testuser1',
                'email': 'testuser1@example.com',
                'first_name': 'Test',
                'last_name': 'User One',
                'mobile': '+919876543210',
                'password': 'testpass123',
            },
            {
                'username': 'testuser2',
                'email': 'testuser2@example.com',
                'first_name': 'Test',
                'last_name': 'User Two',
                'mobile': '+919876543211',
                'password': 'testpass123',
            },
            {
                'username': 'testuser3',
                'email': 'testuser3@example.com',
                'first_name': 'Test',
                'last_name': 'User Three',
                'mobile': '+919876543212',
                'password': 'testpass123',
            },
            {
                'username': 'razorpay_test',
                'email': 'razorpay.test@example.com',
                'first_name': 'Razorpay',
                'last_name': 'Test User',
                'mobile': '+919876543213',
                'password': 'testpass123',
            },
            {
                'username': 'payment_test',
                'email': 'payment.test@example.com',
                'first_name': 'Payment',
                'last_name': 'Test User',
                'mobile': '+919876543214',
                'password': 'testpass123',
            },
        ]

        created_users = []
        updated_users = []

        # Create users (up to count)
        for i, user_data in enumerate(test_users_data[:count]):
            email = user_data['email']
            
            # Check if user already exists
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': user_data['username'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'mobile': user_data['mobile'],
                    'is_active': True,
                    'is_verified': True,
                }
            )

            # Set password
            user.set_password(user_data['password'])
            # Ensure razorpay_customer_id is None (will be created on first payment)
            user.razorpay_customer_id = None
            user.save()

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created user: {user.email}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  User already exists: {user.email}')
                )

            # Create PaymentPreference for the user
            PaymentPreference.objects.get_or_create(
                user=user,
                defaults={
                    'preferred_method': 'card',
                }
            )

            # Create a test address for the user
            Address.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': f"{user.first_name} {user.last_name}",
                    'phone': user.mobile or '+919876543210',
                    'street_address': '123 Test Street, Test Apartment',
                    'city': 'Mumbai',
                    'state': 'Maharashtra',
                    'postal_code': '400001',
                    'country': 'India',
                    'type': 'home',
                    'is_default': True,
                }
            )

            if created:
                created_users.append(user)
            else:
                updated_users.append(user)

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Test Users Seeded Successfully!'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'\n📊 Summary:')
        self.stdout.write(f'   - Created: {len(created_users)} users')
        self.stdout.write(f'   - Updated: {len(updated_users)} users')
        self.stdout.write(f'   - Total: {len(created_users) + len(updated_users)} users')
        
        self.stdout.write('\n🔑 Login Credentials:')
        self.stdout.write('=' * 60)
        for user in created_users + updated_users:
            self.stdout.write(f'   Email: {user.email}')
            self.stdout.write(f'   Password: testpass123')
            self.stdout.write('')
        
        self.stdout.write('=' * 60)
        self.stdout.write('\n💡 You can now:')
        self.stdout.write('   1. Login with any test user')
        self.stdout.write('   2. Test Razorpay payment flow')
        self.stdout.write('   3. Real Razorpay customer ID will be created automatically')
        self.stdout.write('      on first payment attempt (not at login)')
        self.stdout.write('   4. Test saved cards functionality after first payment')
        self.stdout.write('=' * 60)
        self.stdout.write('\n⚠️  Note: Razorpay customer IDs are NOT created during seeding.')
        self.stdout.write('   They will be created automatically when user attempts their first payment.')
        self.stdout.write('=' * 60)

