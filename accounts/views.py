from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import random
import string
import os
from .models import User, OTPVerification, PasswordResetToken, ContactQuery, BulkOrder, PaymentPreference, DataRequest, Vendor
from .serializers import (
    UserLoginSerializer, UserRegistrationSerializer, UserSerializer,
    OTPRequestSerializer, OTPVerificationSerializer, OTPResendSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    ChangePasswordSerializer, ContactQuerySerializer, ContactQueryCreateSerializer,
    BulkOrderSerializer, BulkOrderCreateSerializer, PaymentPreferenceSerializer,
    DataRequestSerializer, DataRequestCreateSerializer,
    VendorRegistrationSerializer, VendorSerializer, VendorLoginSerializer
)
from .data_export_utils import export_orders_to_excel, export_addresses_to_excel, export_payment_options_to_excel
from .gmail_oauth_service import GmailOAuth2Service
from .whatsapp_service import WhatsAppService


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """User login endpoint"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        
        # Generate or get existing token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'error': 'Invalid credentials'
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """User logout endpoint"""
    try:
        # Delete the token
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Logout failed'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_otp_view(request):
    """Request OTP for registration"""
    serializer = OTPRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    email = data['email']
    otp_method = data['otp_method']
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        return Response({
            'success': False,
            'error': 'User with this email already exists'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate 6-digit OTP
    otp_code = ''.join(random.choices(string.digits, k=6))
    
    # Set expiration time (10 minutes)
    expires_at = timezone.now() + timezone.timedelta(minutes=10)
    
    # Create OTP record
    otp_obj = OTPVerification.objects.create(
        email=email,
        mobile=data.get('mobile'),
        otp_code=otp_code,
        otp_method=otp_method,
        expires_at=expires_at,
        user_data={
            'username': data['username'],
            'first_name': data['first_name'],
            'last_name': data.get('last_name', ''),
            'password': data['password'],
            'mobile': data.get('mobile', '')
        }
    )
    
    # Send OTP
    try:
        if otp_method == 'email':
            # Send email OTP using Gmail OAuth service
            gmail_service = GmailOAuth2Service()
            gmail_service.send_otp_email(email, otp_code)
        elif otp_method == 'whatsapp':
            # Send WhatsApp OTP using WhatsApp service
            whatsapp_service = WhatsAppService()
            whatsapp_service.send_otp_message(data['mobile'], otp_code)
        
        return Response({
            'success': True,
            'message': f'OTP sent to your {otp_method}',
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to send OTP: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_view(request):
    """Verify OTP and complete registration"""
    serializer = OTPVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    email = data['email']
    otp = data['otp']
    
    try:
        # Find the most recent OTP for this email
        otp_obj = OTPVerification.objects.filter(
            email=email,
            otp_code=otp,
            is_used=False
        ).order_by('-created_at').first()
        
        if not otp_obj:
            return Response({
                'success': False,
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if otp_obj.is_expired():
            return Response({
                'success': False,
                'error': 'OTP has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark OTP as used
        otp_obj.is_used = True
        otp_obj.is_verified = True
        otp_obj.save()
        
        # Create user from stored data
        user_data = otp_obj.user_data
        user = User.objects.create_user(
            username=user_data['username'],
            email=email,
            first_name=user_data['first_name'],
            last_name=user_data.get('last_name', ''),
            mobile=user_data.get('mobile', ''),
            password=user_data['password'],
            is_verified=True
        )
        
        # Associate OTP with user
        otp_obj.user = user
        otp_obj.save()
        
        # Generate token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'success': True,
            'message': 'Registration successful',
            'user': UserSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Registration failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp_view(request):
    """Resend OTP for registration"""
    serializer = OTPResendSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    email = data['email']
    otp_method = data['otp_method']
    
    try:
        # Find the most recent OTP for this email
        otp_obj = OTPVerification.objects.filter(
            email=email,
            otp_method=otp_method,
            is_used=False
        ).order_by('-created_at').first()
        
        if not otp_obj:
            return Response({
                'success': False,
                'error': 'No pending OTP found for this email'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate new OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        otp_obj.otp_code = otp_code
        otp_obj.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        otp_obj.save()
        
        # Send OTP
        if otp_method == 'email':
            # Send email OTP using Gmail OAuth service
            gmail_service = GmailOAuth2Service()
            gmail_service.send_otp_email(email, otp_code)
        elif otp_method == 'whatsapp':
            # Send WhatsApp OTP using WhatsApp service
            whatsapp_service = WhatsAppService()
            whatsapp_service.send_otp_message(otp_obj.mobile, otp_code)
        
        return Response({
            'success': True,
            'message': f'OTP resent to your {otp_method}',
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to resend OTP: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """Request password reset"""
    serializer = PasswordResetRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    
    try:
        user = User.objects.get(email=email)
        
        # Generate reset token
        token = PasswordResetToken.generate_token()
        expires_at = timezone.now() + timezone.timedelta(hours=1)
        
        # Create or update reset token
        reset_token, created = PasswordResetToken.objects.update_or_create(
            user=user,
            defaults={
                'token': token,
                'expires_at': expires_at,
                'is_used': False
            }
        )
        
        # Send reset email using Gmail OAuth service
        reset_url = f"{settings.FRONTEND_URL}/forgot-password?token={token}"
        gmail_service = GmailOAuth2Service()
        subject = 'Sixpine - Password Reset'
        message = f"""Dear User,

Click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Best regards,
Sixpine Team"""
        gmail_service.send_email(email, subject, message)
        
        return Response({
            'success': True,
            'message': 'Password reset link sent to your email',
            'debug_token': token  # Only for development
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'No user found with this email address'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to send reset email: {str(e)}',
            'debug_token': token  # Still return token for development
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    """Confirm password reset"""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    token = data['token']
    new_password = data['new_password']
    
    try:
        reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
        
        if reset_token.is_expired():
            return Response({
                'success': False,
                'error': 'Reset token has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update user password
        user = reset_token.user
        user.set_password(new_password)
        user.save()
        
        # Mark token as used
        reset_token.is_used = True
        reset_token.save()
        
        return Response({
            'success': True,
            'message': 'Password reset successful'
        }, status=status.HTTP_200_OK)
        
    except PasswordResetToken.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Invalid or expired reset token'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Password reset failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """Get user profile"""
    return Response({
        'success': True,
        'user': UserSerializer(request.user).data
    }, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    """Update user profile"""
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'error': 'Invalid data',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """Change user password"""
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    new_password = data['new_password']
    
    try:
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        return Response({
            'success': True,
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Password change failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def contact_form_submit(request):
    """Submit contact form from home page"""
    try:
        serializer = ContactQueryCreateSerializer(data=request.data)
        if serializer.is_valid():
            contact_query = serializer.save()
            return Response({
                'success': True,
                'message': 'Thank you for contacting us! Our team will reach out to you soon.',
                'data': ContactQuerySerializer(contact_query).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'error': 'Invalid data provided',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to submit contact form: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def bulk_order_submit(request):
    """Submit bulk order inquiry"""
    try:
        serializer = BulkOrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            bulk_order = serializer.save()
            return Response({
                'success': True,
                'message': 'Thank you for your inquiry! Our sales team will contact you shortly.',
                'data': BulkOrderSerializer(bulk_order).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'error': 'Invalid data provided',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to submit bulk order: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= Payment Preferences APIs =============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_preference(request):
    """Get user's payment preference"""
    try:
        preference, created = PaymentPreference.objects.get_or_create(
            user=request.user,
            defaults={'preferred_method': 'card'}
        )
        serializer = PaymentPreferenceSerializer(preference)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to get payment preference: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_payment_preference(request):
    """Update user's payment preference - address is managed via Address table"""
    try:
        preference, _ = PaymentPreference.objects.get_or_create(user=request.user)
        serializer = PaymentPreferenceSerializer(preference, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Payment preference updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to update payment preference: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_saved_cards(request):
    """Get saved cards - fetch from Razorpay and sync with database"""
    import razorpay
    from django.conf import settings
    from .models import SavedCard
    from .serializers import SavedCardSerializer
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get customer_id from User model (not PaymentPreference)
        customer_id = request.user.razorpay_customer_id
        
        if not customer_id:
            return Response({
                'success': True,
                'customer_id': '',
                'saved_cards': [],
                'count': 0,
                'message': 'No customer ID found. Cards will be saved after first payment.'
            }, status=status.HTTP_200_OK)
        
        # Fetch active tokens from Razorpay
        razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', '').strip()
        razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '').strip()
        
        active_tokens = []
        
        if razorpay_key_id and razorpay_key_secret:
            try:
                # Fix for 'Session' object has no attribute 'GET' error
                # Use requests library directly instead of razorpay_client.request()
                import requests
                import base64
                tokens_url = f'https://api.razorpay.com/v1/customers/{customer_id}/tokens'
                # Razorpay uses Basic auth with key:secret
                auth_string = f'{razorpay_key_id}:{razorpay_key_secret}'
                auth_bytes = auth_string.encode('utf-8')
                auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
                headers = {
                    'Authorization': f'Basic {auth_b64}',
                    'Content-Type': 'application/json'
                }
                response = requests.get(tokens_url, headers=headers)
                response.raise_for_status()
                tokens_data = response.json()
                tokens = tokens_data.get('items', [])
                
                logger.info(f'Fetched {len(tokens)} tokens from Razorpay for customer {customer_id}')
                
                # Log all token statuses for debugging
                print(f'[RAZORPAY] Fetched {len(tokens)} tokens from Razorpay API: https://api.razorpay.com/v1/customers/{customer_id}/tokens')
                for idx, token in enumerate(tokens):
                    token_status = token.get('status', 'unknown')
                    token_method = token.get('method', 'unknown')
                    token_id = token.get('id', 'unknown')
                    print(f'[RAZORPAY] Token {idx+1}: id={token_id}, method={token_method}, status={token_status}')
                
                # Filter only active tokens (status should be active, not failed)
                for token in tokens:
                    token_status = token.get('status', '').lower()
                    token_method = token.get('method', '')
                    
                    # Only include active card tokens
                    if token_method == 'card' and token_status in ['active', 'activated']:
                        card = token.get('card', {})
                        token_id = token.get('id')
                        
                        # Sync with database - update or create
                        SavedCard.objects.update_or_create(
                            token_id=token_id,
                            user=request.user,
                            defaults={
                                'customer_id': customer_id,
                                'card_last4': str(card.get('last4', '')),
                                'card_network': card.get('network', ''),
                                'card_type': card.get('type', ''),
                                'card_issuer': card.get('issuer', ''),
                            }
                        )
                        
                        active_tokens.append({
                            'token_id': token_id,
                            'method': token_method,
                            'card': {
                                'last4': str(card.get('last4', '')),
                                'network': card.get('network', ''),
                                'type': card.get('type', ''),
                                'issuer': card.get('issuer', ''),
                                'name': card.get('name', ''),
                                'expiry_month': str(card.get('expiry_month', '')).zfill(2) if card.get('expiry_month') else '',
                                'expiry_year': str(card.get('expiry_year', '')),
                            },
                            'status': token_status,
                            'created_at': token.get('created_at', 0)
                        })
                
                logger.info(f'Found {len(active_tokens)} active tokens')
                print(f'[RAZORPAY] Found {len(active_tokens)} active tokens after filtering')
                
                # Clean up inactive tokens from database
                # Only keep tokens that are active in Razorpay
                if len(active_tokens) > 0:
                    active_token_ids = [token['token_id'] for token in active_tokens]
                    # Delete any saved cards in database that are not in active tokens list
                    inactive_cards = SavedCard.objects.filter(user=request.user).exclude(token_id__in=active_token_ids)
                    if inactive_cards.exists():
                        inactive_count = inactive_cards.count()
                        inactive_cards.delete()
                        print(f'[RAZORPAY] 🗑️  Removed {inactive_count} inactive cards from database')
                        logger.info(f'Removed {inactive_count} inactive cards from database')
                
                # If active tokens exist from Razorpay, use those (don't use database fallback)
                # Only use database fallback if Razorpay API fails completely
                if len(active_tokens) == 0:
                    print(f'[RAZORPAY] ⚠️  No active tokens from Razorpay API')
                    logger.warning(f'No active tokens from Razorpay API')
                
            except Exception as e:
                logger.warning(f'Failed to fetch tokens from Razorpay: {str(e)}')
                print(f'[RAZORPAY] ⚠️  Failed to fetch tokens from Razorpay: {str(e)}')
                # Don't use database fallback - only show cards that are verified active in Razorpay
                # This ensures we only show cards that are actually active
                active_tokens = []
                print(f'[RAZORPAY] ⚠️  Not using database fallback - only showing verified active tokens from Razorpay')
        
        return Response({
            'success': True,
            'customer_id': customer_id,
            'saved_cards': active_tokens,
            'count': len(active_tokens),
            'message': f'Found {len(active_tokens)} active saved cards' if active_tokens else 'No active saved cards found'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to get saved cards: {str(e)}')
        return Response({
            'success': False,
            'error': f'Failed to get saved cards: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_saved_card(request, token_id):
    """Delete a saved card from database and Razorpay"""
    import razorpay
    from django.conf import settings
    from .models import SavedCard
    
    try:
        # Get payment preference (needed for clearing preferred card)
        try:
            preference = PaymentPreference.objects.get(user=request.user)
        except PaymentPreference.DoesNotExist:
            preference = None
        
        # Delete from our database first
        try:
            saved_card = SavedCard.objects.get(token_id=token_id, user=request.user)
            saved_card.delete()
        except SavedCard.DoesNotExist:
            pass  # Card might not exist in DB, continue to delete from Razorpay
        
        # Also delete from Razorpay if configured
        # Use customer_id from User model (not PaymentPreference)
        customer_id = request.user.razorpay_customer_id
        razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', '').strip()
        razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '').strip()
        
        if razorpay_key_id and razorpay_key_secret and customer_id:
            try:
                razorpay_client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
                
                try:
                    # Delete token from Razorpay
                    # Maps to: DELETE /v1/customers/{customer_id}/tokens/{token_id}
                    razorpay_client.customer.delete_token(customer_id, token_id)
                except Exception as e:
                    # Log but don't fail if Razorpay deletion fails
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'Failed to delete token from Razorpay: {str(e)}')
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to delete from Razorpay: {str(e)}')
        
        # Clear preferred card if it was this one
        if preference and preference.preferred_card_token_id == token_id:
            preference.preferred_card_token_id = None
            preference.save()
        
        return Response({
            'success': True,
            'message': 'Card removed successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to delete saved card: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_data_request(request):
    """Create a data request"""
    try:
        serializer = DataRequestCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Check if user already has a pending or approved request of this type
            # Allow new requests if previous one is completed
            existing = DataRequest.objects.filter(
                user=request.user,
                request_type=serializer.validated_data['request_type'],
                status__in=['pending', 'approved']
            ).first()
            
            if existing:
                return Response({
                    'success': False,
                    'error': 'You already have a pending or approved request for this data type. Please download it first or wait for approval.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data_request = DataRequest.objects.create(
                user=request.user,
                request_type=serializer.validated_data['request_type']
            )
            
            return Response({
                'success': True,
                'message': 'Data request submitted successfully',
                'data': DataRequestSerializer(data_request).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to create data request: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_data_requests(request):
    """Get current user's data requests"""
    try:
        data_requests = DataRequest.objects.filter(user=request.user).order_by('-requested_at')
        serializer = DataRequestSerializer(data_requests, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to fetch data requests: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_data_file(request, request_id):
    """Download approved data file - users can download their own files, admins can download any"""
    try:
        data_request = DataRequest.objects.get(id=request_id)
        
        # Check if user owns the request or is admin
        if data_request.user != request.user and not request.user.is_staff:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if request is approved and file exists
        if data_request.status != 'approved' and data_request.status != 'completed':
            return Response({
                'success': False,
                'error': 'Request is not approved yet'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not data_request.file_path or not os.path.exists(data_request.file_path):
            return Response({
                'success': False,
                'error': 'File not found. Please contact admin.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        from django.http import FileResponse
        
        file_name = os.path.basename(data_request.file_path)
        response = FileResponse(open(data_request.file_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        
        # Mark as completed if it was approved
        if data_request.status == 'approved':
            data_request.status = 'completed'
            data_request.completed_at = timezone.now()
            data_request.save()
        
        return response
        
    except DataRequest.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Data request not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to download file: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_account_deletion_eligibility(request):
    """Check if user can delete their account (no pending/ongoing orders)"""
    try:
        from orders.models import Order
        
        # Check for pending, confirmed, processing, or shipped orders (ongoing orders)
        ongoing_orders = Order.objects.filter(
            user=request.user,
            status__in=['pending', 'confirmed', 'processing', 'shipped']
        ).count()
        
        return Response({
            'success': True,
            'can_delete': ongoing_orders == 0,
            'ongoing_orders_count': ongoing_orders,
            'message': f'You have {ongoing_orders} ongoing or pending order(s). Please complete or cancel them before closing your account.' if ongoing_orders > 0 else 'You can close your account.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to check account deletion eligibility: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def close_account(request):
    """Close user account permanently - only if no ongoing/pending orders"""
    try:
        from orders.models import Order
        
        # Check for ongoing orders
        ongoing_orders = Order.objects.filter(
            user=request.user,
            status__in=['pending', 'confirmed', 'processing', 'shipped']
        )
        
        if ongoing_orders.exists():
            order_count = ongoing_orders.count()
            return Response({
                'success': False,
                'error': f'Cannot close account. You have {order_count} ongoing or pending order(s). Please complete or cancel them before closing your account.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get reason if provided
        reason = request.data.get('reason', '')
        
        # Deactivate the account (soft delete - set is_active to False)
        # We don't hard delete to maintain order history for legal/tax purposes
        request.user.is_active = False
        request.user.save()
        
        # Logout the user
        logout(request)
        
        return Response({
            'success': True,
            'message': 'Your account has been closed successfully. You have been logged out.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Failed to close account: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== Vendor Authentication Views ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def vendor_register_view(request):
    """Vendor registration endpoint"""
    serializer = VendorRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        vendor = serializer.save()
        return Response({
            'success': True,
            'message': 'Vendor registration successful. Your account is pending approval.',
            'vendor': VendorSerializer(vendor).data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'error': 'Registration failed',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def vendor_login_view(request):
    """Vendor login endpoint"""
    serializer = VendorLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        vendor = serializer.validated_data['vendor']
        login(request, user)
        
        # Generate or get existing token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'vendor': VendorSerializer(vendor).data,
            'token': token.key
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'error': serializer.errors.get('non_field_errors', ['Invalid credentials'])[0]
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vendor_profile_view(request):
    """Get vendor profile"""
    if not hasattr(request.user, 'vendor_profile'):
        return Response({
            'success': False,
            'error': 'User is not a vendor'
        }, status=status.HTTP_403_FORBIDDEN)
    
    vendor = request.user.vendor_profile
    return Response({
        'success': True,
        'vendor': VendorSerializer(vendor).data
    }, status=status.HTTP_200_OK)