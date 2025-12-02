from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Reset admin password to admin123'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the admin user to reset password for',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username of the admin user to reset password for',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        username = options.get('username')
        
        # Find admin user
        if email:
            try:
                user = User.objects.get(email=email, is_staff=True)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Admin user with email {email} not found'))
                return
        elif username:
            try:
                user = User.objects.get(username=username, is_staff=True)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Admin user with username {username} not found'))
                return
        else:
            # Find first superuser or staff user
            user = User.objects.filter(is_staff=True).first()
            if not user:
                user = User.objects.filter(is_superuser=True).first()
            
            if not user:
                self.stdout.write(self.style.ERROR('No admin user found. Please specify --email or --username'))
                return
        
        # Reset password
        new_password = 'admin123'
        user.set_password(new_password)
        user.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully reset password for admin user: {user.email} (username: {user.username})'
        ))
        self.stdout.write(self.style.SUCCESS(f'New password: {new_password}'))

