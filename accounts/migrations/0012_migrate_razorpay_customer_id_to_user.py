# Generated migration to migrate razorpay_customer_id from PaymentPreference to User model

from django.db import migrations


def migrate_razorpay_customer_id(apps, schema_editor):
    """Migrate razorpay_customer_id from PaymentPreference to User model"""
    User = apps.get_model('accounts', 'User')
    PaymentPreference = apps.get_model('accounts', 'PaymentPreference')
    
    # Migrate customer_id from PaymentPreference to User
    for preference in PaymentPreference.objects.filter(razorpay_customer_id__isnull=False).exclude(razorpay_customer_id=''):
        user = preference.user
        if user and not user.razorpay_customer_id:
            user.razorpay_customer_id = preference.razorpay_customer_id
            user.save(update_fields=['razorpay_customer_id'])


def reverse_migrate_razorpay_customer_id(apps, schema_editor):
    """Reverse migration - copy customer_id back to PaymentPreference"""
    User = apps.get_model('accounts', 'User')
    PaymentPreference = apps.get_model('accounts', 'PaymentPreference')
    
    # Copy customer_id back to PaymentPreference (for rollback purposes)
    for user in User.objects.filter(razorpay_customer_id__isnull=False).exclude(razorpay_customer_id=''):
        try:
            preference = PaymentPreference.objects.get(user=user)
            if not preference.razorpay_customer_id:
                preference.razorpay_customer_id = user.razorpay_customer_id
                preference.save(update_fields=['razorpay_customer_id'])
        except PaymentPreference.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_add_razorpay_customer_id_to_user'),
    ]

    operations = [
        migrations.RunPython(migrate_razorpay_customer_id, reverse_migrate_razorpay_customer_id),
    ]

