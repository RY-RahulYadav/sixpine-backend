from rest_framework import serializers
from .models import Address, Order, OrderItem, OrderStatusHistory, OrderNote, ReturnRequest
from products.serializers import ProductListSerializer, ProductVariantSerializer


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'type', 'full_name', 'phone', 'street_address', 'city', 'state', 
                 'postal_code', 'country', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'variant', 'variant_id', 
                 'variant_color', 'variant_size', 'variant_pattern',
                 'quantity', 'price', 'total_price', 'created_at']
        read_only_fields = ['price', 'total_price', 'variant_color', 'variant_size', 'variant_pattern', 'created_at']


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'notes', 'created_at', 'created_by']
        read_only_fields = ['created_at', 'created_by']


class OrderNoteSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = OrderNote
        fields = ['id', 'content', 'created_at', 'created_by']
        read_only_fields = ['created_at', 'created_by']
    
    def get_created_by(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username
            }
        return None


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for order list view"""
    items = OrderItemSerializer(many=True, read_only=True)
    items_count = serializers.ReadOnlyField()
    shipping_address = AddressSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['order_id', 'status', 'payment_status', 'payment_method', 'total_amount', 'items_count',
                 'shipping_address', 'items', 'created_at', 'estimated_delivery']
        read_only_fields = ['order_id', 'created_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for order detail view"""
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    items_count = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = ['order_id', 'user', 'status', 'payment_status', 'payment_method', 'subtotal', 'coupon', 'coupon_discount',
                 'shipping_cost', 'platform_fee', 'tax_amount', 'total_amount', 'shipping_address', 'tracking_number',
                 'estimated_delivery', 'delivered_at', 'order_notes', 'items', 'status_history',
                 'items_count', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature',
                 'created_at', 'updated_at']
        read_only_fields = ['order_id', 'user', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Add coupon information to response"""
        data = super().to_representation(instance)
        # Include coupon information
        if instance.coupon:
            data['coupon'] = {
                'id': instance.coupon.id,
                'code': instance.coupon.code,
                'discount_type': instance.coupon.discount_type,
                'discount_value': str(instance.coupon.discount_value),
            }
        else:
            data['coupon'] = None
        # Add tax rate from global settings for display
        from admin_api.models import GlobalSettings
        tax_rate = GlobalSettings.get_setting('tax_rate', '5.00')
        data['tax_rate'] = str(tax_rate)
        return data


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders"""
    shipping_address_id = serializers.IntegerField(write_only=True)
    items = OrderItemSerializer(many=True, write_only=True)
    coupon_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Order
        fields = ['shipping_address_id', 'items', 'order_notes', 'coupon_id', 'payment_method']
        
    def validate_shipping_address_id(self, value):
        user = self.context['request'].user
        if not Address.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Invalid shipping address")
        return value

    def create(self, validated_data):
        from products.models import Product, Coupon
        from decimal import Decimal
        
        user = self.context['request'].user
        items_data = validated_data.pop('items')
        shipping_address_id = validated_data.pop('shipping_address_id')
        coupon_id = validated_data.pop('coupon_id', None)
        payment_method = validated_data.pop('payment_method', 'COD')
        
        # Calculate totals
        subtotal = Decimal('0.00')
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            subtotal += product.price * item_data['quantity']
        
        from .utils import calculate_order_totals
        
        # Calculate initial totals (before coupon discount)
        initial_totals = calculate_order_totals(subtotal, payment_method)
        
        # Handle coupon if provided
        coupon = None
        coupon_discount = Decimal('0.00')
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                can_use, message = coupon.can_be_used_by_user(user)
                if can_use:
                    # Seller coupons: discount on platform fee and tax only
                    if coupon.coupon_type == 'seller':
                        discount_amount, discount_message = coupon.calculate_discount(
                            subtotal, 
                            platform_fee=initial_totals['platform_fee'],
                            tax_amount=initial_totals['tax_amount']
                        )
                        coupon_discount = Decimal(str(discount_amount))
                        # For seller coupons, discount is applied to total, not subtotal
                        # The discount reduces platform fee and tax, so we adjust totals
                        totals = {
                            'subtotal': subtotal,  # Subtotal remains unchanged
                            'platform_fee': initial_totals['platform_fee'],
                            'tax_amount': initial_totals['tax_amount'],
                            'shipping_cost': initial_totals['shipping_cost'],
                            'total_amount': subtotal + initial_totals['platform_fee'] + initial_totals['tax_amount'] - coupon_discount
                        }
                    else:
                        # Sixpine and common coupons: discount on product prices
                        if coupon.vendor:
                            vendor_subtotal = Decimal('0.00')
                            for item_data in items_data:
                                product = Product.objects.get(id=item_data['product_id'])
                                if product.vendor and product.vendor.id == coupon.vendor.id:
                                    vendor_subtotal += product.price * item_data['quantity']
                            
                            if vendor_subtotal == 0:
                                raise serializers.ValidationError({
                                    'coupon_id': f'This coupon applies only to products from {coupon.vendor.brand_name}. Please add products from this vendor to your cart.'
                                })
                            
                            discount_amount, _ = coupon.calculate_discount(subtotal, vendor_subtotal)
                        else:
                            discount_amount, _ = coupon.calculate_discount(subtotal)
                        
                        coupon_discount = Decimal(str(discount_amount))
                        # Calculate totals with platform fee (after coupon discount on subtotal)
                        subtotal_after_discount = subtotal - coupon_discount
                        totals = calculate_order_totals(subtotal_after_discount, payment_method)
                    
                    # Update coupon usage
                    coupon.used_count += 1
                    coupon.save()
                else:
                    raise serializers.ValidationError({'coupon_id': message})
            except Coupon.DoesNotExist:
                raise serializers.ValidationError({'coupon_id': 'Invalid coupon'})
        else:
            # No coupon: use initial totals
            totals = initial_totals
        
        # Create order with all required fields stored in database
        order = Order.objects.create(
            user=user,
            shipping_address_id=shipping_address_id,
            subtotal=subtotal,  # Store original subtotal
            coupon=coupon,  # Store coupon reference
            coupon_discount=coupon_discount,  # Store coupon discount amount
            shipping_cost=totals['shipping_cost'],  # Store shipping cost
            platform_fee=totals['platform_fee'],  # Store platform fee
            tax_amount=totals['tax_amount'],  # Store tax amount
            total_amount=totals['total_amount'],  # Store total amount
            payment_method=payment_method,
            **validated_data
        )
        
        # Create order items
        from products.models import ProductVariant
        
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            variant_id = item_data.get('variant_id')
            variant = None
            
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id, product=product)
                except ProductVariant.DoesNotExist:
                    pass
            
            # Get price from variant if available
            price = product.price
            if variant and variant.price:
                price = variant.price
            
            # Get vendor from product
            vendor = product.vendor if hasattr(product, 'vendor') else None
            
            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                vendor=vendor,
                quantity=item_data['quantity'],
                price=price,
                variant_color=variant.color.name if variant else '',
                variant_size=variant.size if variant else '',
                variant_pattern=variant.pattern if variant else ''
            )
            
            # Update variant stock if variant exists
            if variant:
                variant.stock_quantity -= item_data['quantity']
                variant.is_in_stock = variant.stock_quantity > 0
                variant.save()
        
        return order


class ReturnRequestSerializer(serializers.ModelSerializer):
    """Serializer for return requests"""
    order_id = serializers.UUIDField(source='order.order_id', read_only=True)
    order_item_id = serializers.IntegerField(source='order_item.id', read_only=True)
    product_title = serializers.CharField(source='order_item.product.title', read_only=True)
    product_image = serializers.CharField(source='order_item.product.main_image', read_only=True)
    customer_name = serializers.CharField(source='order.user.get_full_name', read_only=True)
    customer_email = serializers.EmailField(source='order.user.email', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)

    class Meta:
        model = ReturnRequest
        fields = [
            'id', 'order', 'order_id', 'order_item', 'order_item_id', 'product_title', 'product_image',
            'reason', 'reason_description', 'pickup_date', 'status', 'seller_approval', 'seller_notes',
            'refund_amount', 'customer_name', 'customer_email', 'created_by_name', 'approved_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'seller_approval', 'refund_amount', 'created_at', 'updated_at', 'created_by', 'approved_by']


class ReturnRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating return requests"""
    order_id = serializers.UUIDField(write_only=True, help_text='Order ID (UUID)')
    
    class Meta:
        model = ReturnRequest
        fields = ['order_id', 'order_item', 'reason', 'reason_description', 'pickup_date']
    
    def validate(self, attrs):
        order_id = attrs.pop('order_id')
        order_item = attrs['order_item']
        
        # Get order by order_id (UUID)
        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            raise serializers.ValidationError({"order_id": "Order not found"})
        
        # Validate that order belongs to the user
        if order.user != self.context['request'].user:
            raise serializers.ValidationError("Order does not belong to you")
        
        # Validate that order item belongs to the order
        if order_item.order != order:
            raise serializers.ValidationError("Order item does not belong to this order")
        
        # Validate that order is delivered (can only return delivered items)
        if order.status != 'delivered':
            raise serializers.ValidationError("Returns can only be requested for delivered orders")
        
        # Check if return window is still valid (10 days from delivery)
        if order.delivered_at:
            from django.utils import timezone
            from datetime import timedelta
            days_since_delivery = (timezone.now().date() - order.delivered_at.date()).days
            if days_since_delivery > 10:
                raise serializers.ValidationError("Return window has expired. Returns must be requested within 10 days of delivery.")
        
        # Check if there's already a pending return request for this item
        existing_return = ReturnRequest.objects.filter(
            order_item=order_item,
            status__in=['pending', 'approved', 'pickup_scheduled']
        ).exists()
        if existing_return:
            raise serializers.ValidationError("A return request already exists for this item")
        
        # Add order to validated_data
        attrs['order'] = order
        return attrs
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)