from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
import razorpay
import hmac
import hashlib
from .models import Address, Order, OrderStatusHistory
from products.models import Coupon
from .serializers import (
    AddressSerializer, OrderListSerializer, OrderDetailSerializer, 
    OrderCreateSerializer
)
from .utils import calculate_order_totals
from admin_api.models import GlobalSettings

# Initialize Razorpay client
razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', '').strip()  # Remove whitespace
razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '').strip()  # Remove whitespace

# Initialize Razorpay client only if keys are provided
if razorpay_key_id and razorpay_key_secret:
    try:
        razorpay_client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
    except Exception as e:
        # Log error but don't crash - let individual views handle it
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to initialize Razorpay client: {str(e)}')
        razorpay_client = None
else:
    razorpay_client = None


class AddressListCreateView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            error_message = str(e)
            if 'protected' in error_message.lower() or 'referenced' in error_message.lower():
                return Response(
                    {'error': 'Cannot delete this address because it is associated with an existing order. Please set a different address as default instead.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'error': 'Failed to delete address. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class OrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related('shipping_address').prefetch_related(
            'items__product', 'items__variant__color'
        )


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'order_id'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'items__product', 'items__variant__color', 'status_history'
        ).select_related('shipping_address')


class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)
        
        # Create initial status history
        OrderStatusHistory.objects.create(
            order=order,
            status='pending',
            notes='Order created',
            created_by=self.request.user
        )
        
        # Clear user's cart after successful order
        from cart.models import Cart
        try:
            cart = Cart.objects.get(user=self.request.user)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            pass


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def checkout_from_cart(request):
    """Create order from user's cart"""
    from cart.models import Cart
    
    shipping_address_id = request.data.get('shipping_address_id')
    order_notes = request.data.get('order_notes', '')
    
    if not shipping_address_id:
        return Response({'error': 'Shipping address is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify shipping address belongs to user
    address = get_object_or_404(Address, id=shipping_address_id, user=request.user)
    
    # Get user's cart
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not cart.items.exists():
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Prepare items data
    items_data = []
    for cart_item in cart.items.all():
        items_data.append({
            'product_id': cart_item.product.id,
            'quantity': cart_item.quantity
        })
    
    # Get coupon_id and payment_method if provided
    coupon_id = request.data.get('coupon_id', None)
    payment_method = request.data.get('payment_method', 'COD')
    
    # Create order
    order_data = {
        'shipping_address_id': shipping_address_id,
        'items': items_data,
        'order_notes': order_notes,
        'coupon_id': coupon_id,
        'payment_method': payment_method
    }
    
    serializer = OrderCreateSerializer(data=order_data, context={'request': request})
    if serializer.is_valid():
        order = serializer.save()
        
        # Create initial status history
        OrderStatusHistory.objects.create(
            order=order,
            status='pending',
            notes='Order created from cart',
            created_by=request.user
        )
        
        # Clear cart
        cart.items.all().delete()
        
        return Response({
            'message': 'Order created successfully',
            'order': OrderDetailSerializer(order, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    if order.status not in ['pending', 'confirmed']:
        return Response({
            'error': 'Order cannot be cancelled at this stage'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    order.status = 'cancelled'
    order.save()
    
    # Create status history
    OrderStatusHistory.objects.create(
        order=order,
        status='cancelled',
        notes='Order cancelled by customer',
        created_by=request.user
    )
    
    # Restore variant stock
    for item in order.items.all():
        if item.variant:
            item.variant.stock_quantity += item.quantity
            item.variant.is_in_stock = item.variant.stock_quantity > 0
            item.variant.save()
    
    return Response({'message': 'Order cancelled successfully'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_razorpay_order(request):
    """Create a Razorpay order for payment"""
    from cart.models import Cart
    
    # Check if Razorpay is enabled
    razorpay_enabled = GlobalSettings.get_setting('razorpay_enabled', True)
    if isinstance(razorpay_enabled, str):
        razorpay_enabled = razorpay_enabled.lower() not in ['false', '0', 'no', '']
    if not razorpay_enabled:
        return Response(
            {'error': 'Razorpay payment gateway is currently disabled. Please use Cash on Delivery or contact support.'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if Razorpay is configured
    if not razorpay_client:
        return Response(
            {'error': 'Razorpay is not configured. Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in environment variables.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    amount = request.data.get('amount')  # Amount in rupees
    shipping_address_id = request.data.get('shipping_address_id')
    
    # Validate required fields
    if amount is None or amount == '':
        return Response(
            {'error': 'Amount is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if shipping_address_id is None or shipping_address_id == '':
        return Response(
            {'error': 'Shipping address ID is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Convert amount to float and validate
        amount_float = float(amount)
        if amount_float <= 0:
            return Response(
                {'error': 'Amount must be greater than 0'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert amount to paise (Razorpay requires amount in smallest currency unit)
        amount_in_paise = int(amount_float * 100)
        
        # Verify address belongs to user
        try:
            address = Address.objects.get(id=shipping_address_id, user=request.user)
        except Address.DoesNotExist:
            return Response(
                {'error': 'Invalid shipping address'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create Razorpay customer for token saving
        # Use User model to store customer_id - created ON FIRST PAYMENT ATTEMPT (not at login)
        # Uses logged-in user's email, name, and phone to create customer
        # This prevents creating new customer_id when user enters different address/name/phone during checkout
        import logging
        logger = logging.getLogger(__name__)
        
        # IMPORTANT: Get customer_id from User model ONLY (not PaymentPreference)
        customer_id = request.user.razorpay_customer_id
        print(f'[RAZORPAY] User {request.user.email} - Current razorpay_customer_id from User model: {customer_id}')
        logger.info(f'User {request.user.email} - Current razorpay_customer_id from User model: {customer_id}')
        
        # Create customer if it doesn't exist (only on first payment attempt)
        if not customer_id or not customer_id.strip():
            # Create customer in Razorpay using logged-in user's email, name, and phone
            try:
                customer_data = {
                    'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email,
                    'email': request.user.email,
                    'contact': request.user.mobile or ''
                }
                print(f'[RAZORPAY] Creating Razorpay customer for {request.user.email} with data: {customer_data}')
                logger.info(f'Creating Razorpay customer for {request.user.email} with data: {customer_data}')
                customer = razorpay_client.customer.create(customer_data)
                customer_id = customer['id']
                # Store in User model (not PaymentPreference)
                request.user.razorpay_customer_id = customer_id
                request.user.save(update_fields=['razorpay_customer_id'])
                print(f'[RAZORPAY] ✅ Created Razorpay customer {customer_id} for user {request.user.email} - Stored in User.razorpay_customer_id')
                logger.info(f'✅ Created Razorpay customer {customer_id} for user {request.user.email} - Stored in User.razorpay_customer_id')
            except Exception as e:
                # If customer creation fails, continue without customer_id
                # Card saving won't work but payment will proceed
                logger.warning(f'Failed to create Razorpay customer: {str(e)}')
                logger.error(f'Customer creation error details: {str(e)}', exc_info=True)
                customer_id = None
        else:
            # Verify customer exists in Razorpay
            try:
                razorpay_client.customer.fetch(customer_id)
            except Exception as e:
                # Customer doesn't exist, create new one
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Customer {customer_id} not found in Razorpay, creating new: {str(e)}')
                try:
                    customer_data = {
                        'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email,
                        'email': request.user.email,
                        'contact': request.user.mobile or ''
                    }
                    customer = razorpay_client.customer.create(customer_data)
                    customer_id = customer['id']
                    # Store in User model (not PaymentPreference)
                    request.user.razorpay_customer_id = customer_id
                    request.user.save(update_fields=['razorpay_customer_id'])
                except Exception as e2:
                    logger.error(f'Failed to create new customer: {str(e2)}')
                    customer_id = None
        
        # Create Razorpay order with customer_id to enable token saving
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': f'order_{request.user.id}_{shipping_address_id}',
            'notes': {
                'user_id': request.user.id,
                'shipping_address_id': shipping_address_id
            }
        }
        
        # Add customer_id to enable card saving (only if valid)
        if customer_id and customer_id.strip():
            order_data['customer_id'] = customer_id.strip()
            print(f'[RAZORPAY] ✅ Adding customer_id {customer_id.strip()} (from User model) to Razorpay order for user {request.user.email}')
            logger.info(f'✅ Adding customer_id {customer_id.strip()} to Razorpay order for user {request.user.email}')
        else:
            print(f'[RAZORPAY] ⚠️  No customer_id available in User model - card saving will not work for user {request.user.email}')
            logger.warning(f'⚠️  No customer_id available - card saving will not work for user {request.user.email}')
        
        print(f'[RAZORPAY] Creating Razorpay order with data: {order_data}')
        logger.info(f'Creating Razorpay order with data: {order_data}')
        razorpay_order = razorpay_client.order.create(order_data)
        print(f'[RAZORPAY] ✅ Created Razorpay order {razorpay_order.get("id")} for user {request.user.email}')
        logger.info(f'✅ Created Razorpay order {razorpay_order.get("id")} for user {request.user.email}')
        
        razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
        
        # Fetch active saved cards for this customer to pass to checkout
        saved_tokens = []
        if customer_id and customer_id.strip():
            try:
                # Fetch active tokens from Razorpay using proper API call
                # Fix for 'Session' object has no attribute 'GET' error
                import requests
                import base64
                razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '').strip()
                tokens_url = f'https://api.razorpay.com/v1/customers/{customer_id.strip()}/tokens'
                # Use requests library directly to avoid Session.GET error
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
                
                # Log all token statuses for debugging
                print(f'[RAZORPAY] Fetched {len(tokens)} tokens from checkout API: https://api.razorpay.com/v1/customers/{customer_id.strip()}/tokens')
                for idx, token in enumerate(tokens):
                    token_status = token.get('status', 'unknown')
                    token_method = token.get('method', 'unknown')
                    token_id = token.get('id', 'unknown')
                    print(f'[RAZORPAY] Token {idx+1}: id={token_id}, method={token_method}, status={token_status}')
                
                # Filter only active card tokens
                for token in tokens:
                    token_status = token.get('status', '').lower()
                    token_method = token.get('method', '')
                    if token_method == 'card' and token_status in ['active', 'activated']:
                        saved_tokens.append({
                            'token_id': token.get('id'),
                            'last4': token.get('card', {}).get('last4', ''),
                            'network': token.get('card', {}).get('network', '')
                        })
            except Exception as e:
                # If fetch fails, continue without saved tokens
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to fetch saved tokens for checkout: {str(e)}')
        
        # Return customer_id and saved tokens so frontend can use them
        response_data = {
            'razorpay_order_id': razorpay_order['id'],
            'amount': amount_float,  # Amount in rupees (frontend will convert to paise)
            'currency': 'INR',
            'key': razorpay_key_id
        }
        
        # Only include customer_id if it's valid (from User model)
        if customer_id and customer_id.strip():
            response_data['customer_id'] = customer_id.strip()
            print(f'[RAZORPAY] ✅ Returning customer_id {customer_id.strip()} (from User model) to frontend for user {request.user.email}')
            logger.info(f'✅ Returning customer_id {customer_id.strip()} to frontend for user {request.user.email}')
            # Include saved tokens for checkout display
            if saved_tokens:
                response_data['saved_tokens'] = saved_tokens
                print(f'[RAZORPAY] ✅ Returning {len(saved_tokens)} saved tokens to frontend')
                logger.info(f'✅ Returning {len(saved_tokens)} saved tokens to frontend')
        else:
            print(f'[RAZORPAY] ⚠️  No customer_id in User model for user {request.user.email} - card saving will not be available')
            logger.warning(f'⚠️  No customer_id available for user {request.user.email} - card saving will not be available')
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response(
            {'error': 'Invalid amount format'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except razorpay.errors.BadRequestError as e:
        error_msg = str(e)
        return Response(
            {'error': f'Razorpay error: {error_msg}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to create Razorpay order: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_razorpay_payment(request):
    """Verify Razorpay payment and create order"""
    from cart.models import Cart
    from decimal import Decimal
    
    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_signature = request.data.get('razorpay_signature')
    shipping_address_id = request.data.get('shipping_address_id')
    payment_method_from_request = request.data.get('payment_method', 'RAZORPAY')
    coupon_id = request.data.get('coupon_id', None)
    
    # Check if Razorpay is enabled
    razorpay_enabled = GlobalSettings.get_setting('razorpay_enabled', True)
    if isinstance(razorpay_enabled, str):
        razorpay_enabled = razorpay_enabled.lower() not in ['false', '0', 'no', '']
    if not razorpay_enabled:
        return Response(
            {'error': 'Razorpay payment gateway is currently disabled. Please use Cash on Delivery or contact support.'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, shipping_address_id]):
        return Response({'error': 'Missing required payment parameters'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Verify payment signature
    try:
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
    except razorpay.SignatureVerificationError:
        # Payment verification failed - create pending order for user to complete payment later
        address = get_object_or_404(Address, id=shipping_address_id, user=request.user)
        
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate totals
        subtotal = Decimal('0.00')
        for cart_item in cart.items.all():
            price = cart_item.product.price
            if cart_item.variant and cart_item.variant.price:
                price = cart_item.variant.price
            subtotal += price * cart_item.quantity
        
        # Handle coupon if provided
        coupon = None
        coupon_discount = Decimal('0.00')
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                can_use, message = coupon.can_be_used_by_user(request.user)
                if can_use:
                    # If coupon is vendor-specific, calculate discount only on vendor's products
                    if coupon.vendor:
                        vendor_subtotal = Decimal('0.00')
                        for cart_item in cart.items.all():
                            if cart_item.product.vendor and cart_item.product.vendor.id == coupon.vendor.id:
                                price = cart_item.product.price
                                if cart_item.variant and cart_item.variant.price:
                                    price = cart_item.variant.price
                                vendor_subtotal += price * cart_item.quantity
                        discount_amount, _ = coupon.calculate_discount(subtotal, vendor_subtotal)
                    else:
                        discount_amount, _ = coupon.calculate_discount(subtotal)
                    coupon_discount = Decimal(str(discount_amount))
                # Don't increment usage for failed verification
            except Coupon.DoesNotExist:
                pass
        
        # Map payment method for platform fee calculation
        payment_method_for_calc = payment_method_from_request.upper() if payment_method_from_request else 'COD'
        
        # Calculate totals with platform fee (after coupon discount)
        subtotal_after_discount = subtotal - coupon_discount
        totals = calculate_order_totals(subtotal_after_discount, payment_method_for_calc)
        
        # Create pending order with payment_status='pending'
        order = Order.objects.create(
            user=request.user,
            shipping_address=address,
            subtotal=subtotal,
            coupon=coupon,
            coupon_discount=coupon_discount,
            shipping_cost=totals['shipping_cost'],
            platform_fee=totals['platform_fee'],
            tax_amount=totals['tax_amount'],
            total_amount=totals['total_amount'],
            payment_method=payment_method_for_calc,
            razorpay_order_id=razorpay_order_id,
            payment_status='pending',
            status='pending'
        )
        
        # Create order items
        for cart_item in cart.items.all():
            from orders.models import OrderItem
            from products.models import ProductVariant
            
            # Get price from variant if available, otherwise from product
            price = cart_item.product.price
            if cart_item.variant and cart_item.variant.price:
                price = cart_item.variant.price
            
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                price=price,
                variant_color=cart_item.variant.color.name if cart_item.variant else '',
                variant_size=cart_item.variant.size if cart_item.variant else '',
                variant_pattern=cart_item.variant.pattern if cart_item.variant else ''
            )
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='pending',
            notes='Order created but payment verification failed. User needs to complete payment.',
            created_by=request.user
        )
        
        # Clear cart even if payment failed (order is created)
        cart.items.all().delete()
        
        return Response({
            'error': 'Payment signature verification failed. Order created with pending payment status.',
            'order_id': str(order.order_id)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify address belongs to user
    address = get_object_or_404(Address, id=shipping_address_id, user=request.user)
    
    # Get cart
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not cart.items.exists():
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Prepare items data
    items_data = []
    for cart_item in cart.items.all():
        items_data.append({
            'product_id': cart_item.product.id,
            'quantity': cart_item.quantity
        })
    
    # Calculate totals
    subtotal = Decimal('0.00')
    for cart_item in cart.items.all():
        price = cart_item.product.price
        if cart_item.variant and cart_item.variant.price:
            price = cart_item.variant.price
        subtotal += price * cart_item.quantity
    
    # Handle coupon if provided
    coupon = None
    coupon_discount = Decimal('0.00')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            can_use, message = coupon.can_be_used_by_user(request.user)
            if can_use:
                # If coupon is vendor-specific, calculate discount only on vendor's products
                if coupon.vendor:
                    vendor_subtotal = Decimal('0.00')
                    for cart_item in cart.items.all():
                        if cart_item.product.vendor and cart_item.product.vendor.id == coupon.vendor.id:
                            price = cart_item.product.price
                            if cart_item.variant and cart_item.variant.price:
                                price = cart_item.variant.price
                            vendor_subtotal += price * cart_item.quantity
                    
                    if vendor_subtotal == 0:
                        return Response({
                            'error': f'This coupon applies only to products from {coupon.vendor.brand_name}. Please add products from this vendor to your cart.'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    discount_amount, _ = coupon.calculate_discount(subtotal, vendor_subtotal)
                else:
                    discount_amount, _ = coupon.calculate_discount(subtotal)
                
                coupon_discount = Decimal(str(discount_amount))
                # Update coupon usage
                coupon.used_count += 1
                coupon.save()
            else:
                return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
        except Coupon.DoesNotExist:
            return Response({'error': 'Invalid coupon'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Map payment method to internal format for platform fee calculation
    # Use payment_method_from_request (from frontend: CC, NB, UPI, etc.) for calculation
    # This ensures platform fee is calculated correctly based on what user selected
    if payment_method_from_request and payment_method_from_request.upper() in ['CC', 'CARD', 'NB', 'NET_BANKING', 'UPI']:
        # Use the payment method from frontend request (CC, NB, UPI, etc.)
        payment_method_for_calc = payment_method_from_request.upper()
    else:
        # Default to CC (Card) if not specified
        payment_method_for_calc = 'CC'
    
    # Calculate totals with platform fee (after coupon discount)
    # Platform fee is calculated based on payment method (CC = 2.36%, UPI = 0%, etc.)
    subtotal_after_discount = subtotal - coupon_discount
    totals = calculate_order_totals(subtotal_after_discount, payment_method_for_calc)
    
    print(f'[PLATFORM_FEE] Calculation for order:')
    print(f'[PLATFORM_FEE]    - Payment Method (from request): {payment_method_from_request}')
    print(f'[PLATFORM_FEE]    - Payment Method (for calc): {payment_method_for_calc}')
    print(f'[PLATFORM_FEE]    - Subtotal after discount: {subtotal_after_discount}')
    print(f'[PLATFORM_FEE]    - Platform Fee: {totals["platform_fee"]}')
    print(f'[PLATFORM_FEE]    - Tax: {totals["tax_amount"]}')
    print(f'[PLATFORM_FEE]    - Total: {totals["total_amount"]}')
    
    # Create order
    order = Order.objects.create(
        user=request.user,
        shipping_address=address,
        subtotal=subtotal,
        coupon=coupon,
        coupon_discount=coupon_discount,
        shipping_cost=totals['shipping_cost'],
        platform_fee=totals['platform_fee'],
        tax_amount=totals['tax_amount'],
        total_amount=totals['total_amount'],
        payment_method=payment_method_for_calc,  # Store the mapped payment method
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
        payment_status='paid',
        status='confirmed'
    )
    
    # Create order items
    for cart_item in cart.items.all():
        from orders.models import OrderItem
        from products.models import ProductVariant
        
        # Get price from variant if available, otherwise from product
        price = cart_item.product.price
        if cart_item.variant and cart_item.variant.price:
            price = cart_item.variant.price
        
        # Get vendor from product
        vendor = cart_item.product.vendor if hasattr(cart_item.product, 'vendor') else None
        
        # Create order item with variant information
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            variant=cart_item.variant,
            vendor=vendor,
            quantity=cart_item.quantity,
            price=price,
            variant_color=cart_item.variant.color.name if cart_item.variant else '',
            variant_size=cart_item.variant.size if cart_item.variant else '',
            variant_pattern=cart_item.variant.pattern if cart_item.variant else ''
        )
        
        # Update variant stock if variant exists
        if cart_item.variant:
            cart_item.variant.stock_quantity -= cart_item.quantity
            cart_item.variant.is_in_stock = cart_item.variant.stock_quantity > 0
            cart_item.variant.save()
    
    # Fetch payment details to get token_id and customer_id if card was saved
    saved_card_info = None
    token_id = None
    payment_method = None
    try:
        payment = razorpay_client.payment.fetch(razorpay_payment_id)
        
        # Get or create payment preference
        from accounts.models import PaymentPreference
        import logging
        logger = logging.getLogger(__name__)
        preference, _ = PaymentPreference.objects.get_or_create(user=request.user)
        
        # Update Razorpay customer ID in User model if not set
        # Use User model to store customer_id (not PaymentPreference)
        if not request.user.razorpay_customer_id:
            if payment.get('customer_id'):
                request.user.razorpay_customer_id = payment['customer_id']
                request.user.save(update_fields=['razorpay_customer_id'])
            elif payment.get('notes', {}).get('customer_id'):
                request.user.razorpay_customer_id = payment['notes']['customer_id']
                request.user.save(update_fields=['razorpay_customer_id'])
        
        # Get customer_id from User model
        customer_id = request.user.razorpay_customer_id
        
        # Check if payment has token_id (card was saved during checkout)
        token_id = payment.get('token_id')
        razorpay_payment_method = payment.get('method')  # From Razorpay: 'card', 'netbanking', 'upi'
        payment_customer_id = payment.get('customer_id')
        payment_card = payment.get('card', {})
        
        # Log full payment details for debugging
        print(f'[RAZORPAY] 🔍 Payment details for user {request.user.email}:')
        print(f'[RAZORPAY]    - Payment ID: {razorpay_payment_id}')
        print(f'[RAZORPAY]    - Razorpay Method: {razorpay_payment_method}')
        print(f'[RAZORPAY]    - Request Method: {payment_method_from_request}')
        print(f'[RAZORPAY]    - Token ID: {token_id}')
        print(f'[RAZORPAY]    - Payment Customer ID: {payment_customer_id}')
        print(f'[RAZORPAY]    - User Customer ID (from User model): {request.user.razorpay_customer_id}')
        print(f'[RAZORPAY]    - Card details: {payment_card}')
        logger.info(f'🔍 Payment details for user {request.user.email}:')
        logger.info(f'   - Payment ID: {razorpay_payment_id}')
        logger.info(f'   - Razorpay Method: {razorpay_payment_method}')
        logger.info(f'   - Request Method: {payment_method_from_request}')
        logger.info(f'   - Token ID: {token_id}')
        logger.info(f'   - Payment Customer ID: {payment_customer_id}')
        logger.info(f'   - User Customer ID (from User model): {request.user.razorpay_customer_id}')
        logger.info(f'   - Card details: {payment_card}')
        
        if token_id and razorpay_payment_method == 'card':
            # Card was saved - token_id is available
            # IMPORTANT: Verify token is active before saving to database
            try:
                # Fetch token details from Razorpay to verify status
                customer_id_for_token = payment_customer_id or request.user.razorpay_customer_id
                if customer_id_for_token:
                    import requests
                    import base64
                    razorpay_key_id_local = getattr(settings, 'RAZORPAY_KEY_ID', '').strip()
                    razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '').strip()
                    token_url = f'https://api.razorpay.com/v1/customers/{customer_id_for_token}/tokens/{token_id}'
                    auth_string = f'{razorpay_key_id_local}:{razorpay_key_secret}'
                    auth_bytes = auth_string.encode('utf-8')
                    auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
                    headers = {
                        'Authorization': f'Basic {auth_b64}',
                        'Content-Type': 'application/json'
                    }
                    token_response = requests.get(token_url, headers=headers)
                    token_response.raise_for_status()
                    token_data = token_response.json()
                    token_status = token_data.get('status', '').lower()
                    
                    print(f'[RAZORPAY] Token {token_id} status from Razorpay: {token_status}')
                    logger.info(f'Token {token_id} status from Razorpay: {token_status}')
                    
                    # Only save card if token status is active
                    if token_status in ['active', 'activated']:
                        print(f'[RAZORPAY] ✅ Token is ACTIVE - saving card to database')
                        logger.info(f'Token is active - saving card to database')
                        
                        # Store card details in SavedCard model
                        from accounts.models import SavedCard
                        card_last4 = payment_card.get('last4', '')
                        card_network = payment_card.get('network', '')
                        card_type = payment_card.get('type', '')
                        card_issuer = payment_card.get('issuer', '')
                        
                        # Create or update saved card - ONLY FOR ACTIVE TOKENS
                        saved_card, created = SavedCard.objects.update_or_create(
                            token_id=token_id,
                            defaults={
                                'user': request.user,
                                'customer_id': customer_id_for_token,
                                'card_last4': card_last4,
                                'card_network': card_network,
                                'card_type': card_type,
                                'card_issuer': card_issuer,
                            }
                        )
                    else:
                        print(f'[RAZORPAY] ⚠️  Token status is {token_status} (not active) - NOT saving to database')
                        logger.warning(f'Token status is {token_status} (not active) - NOT saving card to database')
                        saved_card = None
                        created = False
                else:
                    print(f'[RAZORPAY] ⚠️  No customer_id available - cannot verify token status')
                    logger.warning(f'No customer_id available - cannot verify token status')
                    saved_card = None
                    created = False
            except Exception as e:
                print(f'[RAZORPAY] ⚠️  Failed to verify token status: {str(e)} - NOT saving card')
                logger.warning(f'Failed to verify token status: {str(e)} - NOT saving card')
                saved_card = None
                created = False
            
            # Only process if card was saved (token is active)
            if saved_card:
            
                if created:
                    print(f'[RAZORPAY] ✅ Created new saved card: {saved_card.card_network} ****{saved_card.card_last4}')
                    logger.info(f'Created new saved card: {saved_card.card_network} ****{saved_card.card_last4}')
                else:
                    print(f'[RAZORPAY] ✅ Updated existing saved card: {saved_card.card_network} ****{saved_card.card_last4}')
                    logger.info(f'Updated existing saved card: {saved_card.card_network} ****{saved_card.card_last4}')
                
                # Set as preferred if user doesn't have one set
                if not preference.preferred_card_token_id:
                    preference.preferred_card_token_id = token_id
                    preference.preferred_method = 'card'
                    saved_card.is_default = True
                    saved_card.save()
                    preference.save()
                    print(f'[RAZORPAY] ✅ Set token_id {token_id} as preferred card')
                    logger.info(f'Set token_id {token_id} as preferred card')
                
                # Prepare saved card info for response
                saved_card_info = {
                    'token_id': saved_card.token_id,
                    'card': {
                        'last4': saved_card.card_last4,
                        'network': saved_card.card_network,
                        'type': saved_card.card_type,
                        'issuer': saved_card.card_issuer,
                    }
                }
            else:
                saved_card_info = None
        else:
            # Card was not saved - log why
            if not token_id:
                print(f'[RAZORPAY] ⚠️  No token_id in payment response for user {request.user.email}')
                print(f'[RAZORPAY]    - Payment method: {payment_method}')
                print(f'[RAZORPAY]    - Possible reasons:')
                print(f'[RAZORPAY]      1. User did not check "Save this card" checkbox in Razorpay checkout')
                print(f'[RAZORPAY]      2. Tokenization not enabled in Razorpay account')
                print(f'[RAZORPAY]      3. Customer ID was not passed correctly to Razorpay')
                print(f'[RAZORPAY]      4. Flash Checkout not enabled')
                logger.warning(f'⚠️  No token_id in payment response for user {request.user.email}')
                logger.warning(f'   - Payment method: {payment_method}')
                logger.warning(f'   - Possible reasons:')
                logger.warning(f'     1. User did not check "Save this card" checkbox in Razorpay checkout')
                logger.warning(f'     2. Tokenization not enabled in Razorpay account')
                logger.warning(f'     3. Customer ID was not passed correctly to Razorpay')
                logger.warning(f'     4. Flash Checkout not enabled')
            elif payment_method != 'card':
                print(f'[RAZORPAY] Payment method is {payment_method}, not card - token_id present but method mismatch')
                logger.info(f'Payment method is {payment_method}, not card - token_id present but method mismatch')
        
    except Exception as e:
        # Log error but don't break order creation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error fetching payment details for token: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        pass
    
    # Create initial status history
    OrderStatusHistory.objects.create(
        order=order,
        status='confirmed',
        notes='Order created and payment verified',
        created_by=request.user
    )
    
    # Clear cart
    cart.items.all().delete()
    
    # Return order details
    from .serializers import OrderDetailSerializer
    response_data = {
        'message': 'Order created successfully',
        'order': OrderDetailSerializer(order, context={'request': request}).data
    }
    
    # Include saved card info if card was saved during payment
    if saved_card_info:
        response_data['saved_card'] = saved_card_info
    
    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def complete_payment(request):
    """Complete payment for a pending order"""
    from decimal import Decimal
    
    order_id = request.data.get('order_id')
    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_signature = request.data.get('razorpay_signature')
    payment_method = request.data.get('payment_method', 'RAZORPAY')
    
    if not order_id:
        return Response({'error': 'Order ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get order
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if order is pending payment
    if order.payment_status != 'pending':
        return Response({'error': 'Order payment is already completed or cannot be completed'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Validate payment method availability
    if payment_method in ['RAZORPAY', 'CARD', 'NET_BANKING', 'UPI']:
        razorpay_enabled = GlobalSettings.get_setting('razorpay_enabled', True)
        if isinstance(razorpay_enabled, str):
            razorpay_enabled = razorpay_enabled.lower() not in ['false', '0', 'no', '']
        if not razorpay_enabled:
            return Response(
                {'error': 'Razorpay payment gateway is currently disabled. Please use Cash on Delivery or contact support.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
    elif payment_method == 'COD':
        cod_enabled = GlobalSettings.get_setting('cod_enabled', True)
        if isinstance(cod_enabled, str):
            cod_enabled = cod_enabled.lower() not in ['false', '0', 'no', '']
        if not cod_enabled:
            return Response(
                {'error': 'Cash on Delivery is currently disabled. Please use online payment methods or contact support.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
    
    # Verify payment signature if Razorpay
    if payment_method in ['RAZORPAY', 'CARD', 'NET_BANKING', 'UPI']:
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({'error': 'Missing required payment parameters'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            razorpay_client.utility.verify_payment_signature(params_dict)
        except razorpay.SignatureVerificationError:
            return Response({'error': 'Payment signature verification failed'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update order with payment details
        order.razorpay_order_id = razorpay_order_id
        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature
    
    # Update order status
    order.payment_method = payment_method
    order.payment_status = 'paid'
    order.status = 'confirmed'
    order.save()
    
    # Update variant stock (if not already done and variant exists)
    if order.items.exists():
        for order_item in order.items.all():
            if order_item.variant:
                if order_item.variant.stock_quantity >= order_item.quantity:
                    order_item.variant.stock_quantity -= order_item.quantity
                    order_item.variant.is_in_stock = order_item.variant.stock_quantity > 0
                    order_item.variant.save()
    
    # Create status history
    OrderStatusHistory.objects.create(
        order=order,
        status='confirmed',
        notes='Payment completed successfully. Order confirmed.',
        created_by=request.user
    )
    
    # Return order details
    from .serializers import OrderDetailSerializer
    return Response({
        'message': 'Payment completed successfully. Order confirmed.',
        'order': OrderDetailSerializer(order, context={'request': request}).data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validate_coupon(request):
    """Validate a coupon code for the current user"""
    coupon_code = request.data.get('code', '').strip().upper()
    order_amount = request.data.get('order_amount', 0)
    cart_items = request.data.get('cart_items', [])  # List of {product_id, quantity, price}
    
    if not coupon_code:
        return Response(
            {'error': 'Coupon code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    from decimal import Decimal
    
    try:
        # Convert to Decimal for proper calculation
        order_amount = Decimal(str(order_amount))
    except (ValueError, TypeError, Exception):
        return Response(
            {'error': 'Invalid order amount'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        coupon = Coupon.objects.get(code=coupon_code)
    except Coupon.DoesNotExist:
        return Response(
            {'error': 'Invalid coupon code'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if coupon can be used by user
    can_use, message = coupon.can_be_used_by_user(request.user)
    if not can_use:
        return Response(
            {'error': message},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # If coupon is vendor-specific, validate cart items contain vendor's products
    vendor_products_amount = None
    if coupon.vendor:
        if not cart_items:
            return Response(
                {'error': 'Cart items are required for vendor-specific coupons'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate total amount for vendor's products only
        vendor_products_amount = Decimal('0.00')
        vendor_product_found = False
        
        for item in cart_items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            price = item.get('price', 0)
            
            try:
                from products.models import Product
                product = Product.objects.get(id=product_id)
                # Check if product belongs to coupon's vendor
                if product.vendor and product.vendor.id == coupon.vendor.id:
                    vendor_product_found = True
                    item_total = Decimal(str(price)) * Decimal(str(quantity))
                    vendor_products_amount += item_total
            except Product.DoesNotExist:
                continue
        
        if not vendor_product_found:
            return Response(
                {'error': f'This coupon applies only to products from {coupon.vendor.brand_name}. Please add products from this vendor to your cart.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Calculate discount (on vendor products if vendor-specific, otherwise on total)
    discount_amount, discount_message = coupon.calculate_discount(order_amount, vendor_products_amount)
    
    # Convert Decimal to float for JSON response
    discount_amount = float(discount_amount)
    
    if discount_amount == 0:
        return Response(
            {'error': discount_message},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({
        'success': True,
        'coupon': {
            'id': coupon.id,
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_value': str(coupon.discount_value),
            'discount_amount': round(discount_amount, 2),
            'message': discount_message
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_payment_charges(request):
    """Get payment charges (platform fees and tax rate) - Public endpoint for checkout calculation"""
    def get_setting_value(key, default):
        value = GlobalSettings.get_setting(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        return value
    
    data = {
        'platform_fee_upi': str(GlobalSettings.get_setting('platform_fee_upi', '0.00')),
        'platform_fee_card': str(GlobalSettings.get_setting('platform_fee_card', '2.36')),
        'platform_fee_netbanking': str(GlobalSettings.get_setting('platform_fee_netbanking', '2.36')),
        'platform_fee_cod': str(GlobalSettings.get_setting('platform_fee_cod', '0.00')),
        'tax_rate': str(GlobalSettings.get_setting('tax_rate', '5.00')),
        'razorpay_enabled': get_setting_value('razorpay_enabled', True),
        'cod_enabled': get_setting_value('cod_enabled', True),
        'coupons_enabled': get_setting_value('coupons_enabled', True)
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def checkout_with_cod(request):
    """Checkout with Cash on Delivery"""
    from cart.models import Cart
    from decimal import Decimal
    
    # Check if COD is enabled
    cod_enabled = GlobalSettings.get_setting('cod_enabled', True)
    if isinstance(cod_enabled, str):
        cod_enabled = cod_enabled.lower() not in ['false', '0', 'no', '']
    if not cod_enabled:
        return Response(
            {'error': 'Cash on Delivery is currently disabled. Please use online payment methods or contact support.'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    shipping_address_id = request.data.get('shipping_address_id')
    order_notes = request.data.get('order_notes', '')
    coupon_id = request.data.get('coupon_id', None)
    
    if not shipping_address_id:
        return Response({'error': 'Shipping address is required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Verify address
    address = get_object_or_404(Address, id=shipping_address_id, user=request.user)
    
    # Get cart
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not cart.items.exists():
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Calculate totals
    subtotal = Decimal('0.00')
    for cart_item in cart.items.all():
        price = cart_item.product.price
        if cart_item.variant and cart_item.variant.price:
            price = cart_item.variant.price
        subtotal += price * cart_item.quantity
    
    # Handle coupon if provided
    coupon = None
    coupon_discount = Decimal('0.00')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            can_use, message = coupon.can_be_used_by_user(request.user)
            if can_use:
                # If coupon is vendor-specific, calculate discount only on vendor's products
                if coupon.vendor:
                    vendor_subtotal = Decimal('0.00')
                    for cart_item in cart.items.all():
                        if cart_item.product.vendor and cart_item.product.vendor.id == coupon.vendor.id:
                            price = cart_item.product.price
                            if cart_item.variant and cart_item.variant.price:
                                price = cart_item.variant.price
                            vendor_subtotal += price * cart_item.quantity
                    
                    if vendor_subtotal == 0:
                        return Response({
                            'error': f'This coupon applies only to products from {coupon.vendor.brand_name}. Please add products from this vendor to your cart.'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    discount_amount, _ = coupon.calculate_discount(subtotal, vendor_subtotal)
                else:
                    discount_amount, _ = coupon.calculate_discount(subtotal)
                
                coupon_discount = Decimal(str(discount_amount))
                # Update coupon usage
                coupon.used_count += 1
                coupon.save()
            else:
                return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
        except Coupon.DoesNotExist:
            return Response({'error': 'Invalid coupon'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Calculate totals with platform fee (after coupon discount)
    subtotal_after_discount = subtotal - coupon_discount
    totals = calculate_order_totals(subtotal_after_discount, 'COD')
    
    # Create order
    order = Order.objects.create(
        user=request.user,
        shipping_address=address,
        subtotal=subtotal,
        coupon=coupon,
        coupon_discount=coupon_discount,
        shipping_cost=totals['shipping_cost'],
        platform_fee=totals['platform_fee'],
        tax_amount=totals['tax_amount'],
        total_amount=totals['total_amount'],
        payment_method='COD',
        payment_status='pending',
        status='confirmed',  # COD orders are confirmed immediately, payment is pending
        order_notes=order_notes
    )
    
    # Create order items
    for cart_item in cart.items.all():
        from orders.models import OrderItem
        from products.models import ProductVariant
        
        # Get price from variant if available, otherwise from product
        price = cart_item.product.price
        if cart_item.variant and cart_item.variant.price:
            price = cart_item.variant.price
        
        # Get vendor from product
        vendor = cart_item.product.vendor if hasattr(cart_item.product, 'vendor') else None
        
        # Create order item with variant information
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            variant=cart_item.variant,
            vendor=vendor,
            quantity=cart_item.quantity,
            price=price,
            variant_color=cart_item.variant.color.name if cart_item.variant else '',
            variant_size=cart_item.variant.size if cart_item.variant else '',
            variant_pattern=cart_item.variant.pattern if cart_item.variant else ''
        )
        
        # Update variant stock if variant exists
        if cart_item.variant:
            cart_item.variant.stock_quantity -= cart_item.quantity
            cart_item.variant.is_in_stock = cart_item.variant.stock_quantity > 0
            cart_item.variant.save()
    
    # Create initial status history
    OrderStatusHistory.objects.create(
        order=order,
        status='confirmed',
        notes='Order confirmed with COD payment',
        created_by=request.user
    )
    
    # Clear cart
    cart.items.all().delete()
    
    # Return order details
    from .serializers import OrderDetailSerializer
    return Response({
        'message': 'Order created successfully',
        'order': OrderDetailSerializer(order, context={'request': request}).data
    }, status=status.HTTP_201_CREATED)
