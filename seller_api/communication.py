from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.conf import settings
from accounts.models import User, Vendor
from accounts.brevo_email_service import BrevoEmailService
from admin_api.models import GlobalSettings
from .permissions import IsVendorUser


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVendorUser])
def get_admin_email(request):
    """Get admin email from settings (for seller communication)"""
    try:
        admin_email = GlobalSettings.get_setting('admin_email', None)
        
        # If not set in settings, fallback to first superuser email or DEFAULT_FROM_EMAIL
        if not admin_email:
            admin_users = User.objects.filter(is_staff=True, is_superuser=True, is_active=True)
            if admin_users.exists():
                admin_email = admin_users.first().email
            else:
                admin_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@sixpine.com')
        
        return Response({
            'success': True,
            'admin_email': admin_email
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVendorUser])
def get_customers_list(request):
    """Get list of customers for seller to send emails to"""
    try:
        # Get customers who have placed orders with this vendor's products
        vendor = request.user.vendor_profile
        
        # Get unique customers who have ordered from this vendor
        from orders.models import Order, OrderItem
        customer_ids = OrderItem.objects.filter(
            vendor=vendor
        ).values_list('order__user_id', flat=True).distinct()
        
        customers = User.objects.filter(
            id__in=customer_ids,
            is_staff=False  # Exclude staff/admin users
        ).values('id', 'email', 'first_name', 'last_name', 'username')
        
        customers_list = []
        for customer in customers:
            customers_list.append({
                'id': customer['id'],
                'name': f"{customer['first_name']} {customer['last_name']}".strip() or customer['username'] or 'Customer',
                'email': customer['email'],
                'username': customer['username']
            })
        
        return Response({
            'success': True,
            'customers': customers_list
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsVendorUser])
def seller_send_email(request):
    """Send email from seller to customer or admin"""
    try:
        recipient_type = request.data.get('recipient_type')  # 'customer' or 'admin'
        recipient_id = request.data.get('recipient_id')  # customer ID if recipient_type is 'customer'
        subject = request.data.get('subject', '')
        message = request.data.get('message', '')
        
        if not recipient_type or not subject or not message:
            return Response({
                'success': False,
                'error': 'Missing required fields: recipient_type, subject, and message are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        vendor = request.user.vendor_profile
        brevo_service = BrevoEmailService()
        
        if recipient_type == 'customer':
            if not recipient_id:
                return Response({
                    'success': False,
                    'error': 'recipient_id is required when recipient_type is customer'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                customer = User.objects.get(id=recipient_id, is_staff=False)
                # Verify customer has ordered from this vendor
                from orders.models import OrderItem
                has_ordered = OrderItem.objects.filter(
                    vendor=vendor,
                    order__user=customer
                ).exists()
                
                if not has_ordered:
                    return Response({
                        'success': False,
                        'error': 'You can only send emails to customers who have ordered from you'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                recipient_email = customer.email
                recipient_name = f"{customer.first_name} {customer.last_name}".strip() or customer.username or 'Customer'
                
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Customer not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        elif recipient_type == 'admin':
            # Get admin email from settings first, then fallback to superuser or default
            admin_email = GlobalSettings.get_setting('admin_email', None)
            
            if admin_email:
                recipient_email = admin_email
            else:
                # Fallback to first superuser email
                admin_users = User.objects.filter(is_staff=True, is_superuser=True, is_active=True)
                if admin_users.exists():
                    recipient_email = admin_users.first().email
                else:
                    recipient_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@sixpine.com')
            
            recipient_name = 'Admin'
        else:
            return Response({
                'success': False,
                'error': 'Invalid recipient_type. Must be "customer" or "admin"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare email body
        vendor_name = vendor.brand_name or vendor.business_name or 'Vendor'
        email_body = f"""Dear {recipient_name},

{message}

---
Sent by: {vendor_name}
Email: {request.user.email}
"""
        
        # Send email
        success = brevo_service.send_email(recipient_email, subject, email_body)
        
        if success:
            return Response({
                'success': True,
                'message': f'Email sent successfully to {recipient_name}'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'Failed to send email. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

