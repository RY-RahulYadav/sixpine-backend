from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = 'Debug user password'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email')

    def handle(self, *args, **options):
        email = options['email']
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f"User found: {user.email}")
            self.stdout.write(f"Username: {user.username}")
            self.stdout.write(f"Is active: {user.is_active}")
            self.stdout.write(f"Password check 'testpass123': {user.check_password('testpass123')}")
            self.stdout.write(f"Password check 'newpass123': {user.check_password('newpass123')}")
            self.stdout.write(f"Password check 'debugpass123': {user.check_password('debugpass123')}")
        except User.DoesNotExist:
            self.stdout.write(f"User with email {email} not found")
