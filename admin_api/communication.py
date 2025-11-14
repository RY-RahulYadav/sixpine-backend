from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.models import User, Vendor
from accounts.gmail_oauth_service import GmailOAuth2Service
from .permissions import IsAdminUser


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_customers_list(request):
    """Get list of all customers for admin to send emails to"""
    try:
        customers = User.objects.filter(
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


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_vendors_list(request):
    """Get list of all vendors for admin to send emails to"""
    try:
        # Get all vendors (admin can contact any vendor, not just active ones)
        # Filter by status='active' and is_verified=True (is_active is a property, not a field)
        vendors = Vendor.objects.all().select_related('user').order_by('brand_name', 'business_name')
        
        vendors_list = []
        for vendor in vendors:
            # Get vendor name - prefer brand_name, then business_name, then user email
            vendor_name = vendor.brand_name or vendor.business_name
            if not vendor_name:
                vendor_name = vendor.user.get_full_name() or vendor.user.username or 'Vendor'
            
            vendors_list.append({
                'id': vendor.id,
                'name': vendor_name,
                'email': vendor.user.email,
                'business_name': vendor.business_name or '',
                'brand_name': vendor.brand_name or ''
            })
        
        return Response({
            'success': True,
            'vendors': vendors_list
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_send_email(request):
    """Send email from admin to customer or vendor"""
    try:
        recipient_type = request.data.get('recipient_type')  # 'customer' or 'vendor'
        recipient_id = request.data.get('recipient_id')
        subject = request.data.get('subject', '')
        message = request.data.get('message', '')
        
        if not recipient_type or not recipient_id or not subject or not message:
            return Response({
                'success': False,
                'error': 'Missing required fields: recipient_type, recipient_id, subject, and message are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        gmail_service = GmailOAuth2Service()
        
        if recipient_type == 'customer':
            try:
                customer = User.objects.get(id=recipient_id, is_staff=False)
                recipient_email = customer.email
                recipient_name = f"{customer.first_name} {customer.last_name}".strip() or customer.username or 'Customer'
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Customer not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        elif recipient_type == 'vendor':
            try:
                vendor = Vendor.objects.get(id=recipient_id, is_active=True)
                recipient_email = vendor.user.email
                recipient_name = vendor.brand_name or vendor.business_name or 'Vendor'
            except Vendor.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Vendor not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'success': False,
                'error': 'Invalid recipient_type. Must be "customer" or "vendor"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare email body
        admin_name = request.user.get_full_name() or request.user.username or 'Admin'
        email_body = f"""Dear {recipient_name},

{message}

---
Sent by: {admin_name} (Admin)
Email: {request.user.email}
"""
        
        # Send email
        success = gmail_service.send_email(recipient_email, subject, email_body)
        
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

