from rest_framework import serializers
from .models import Address, Order, OrderItem, OrderStatusHistory, OrderNote
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
        
        # Handle coupon if provided
        coupon = None
        coupon_discount = Decimal('0.00')
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                can_use, message = coupon.can_be_used_by_user(user)
                if can_use:
                    # If coupon is vendor-specific, calculate discount only on vendor's products
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
                    # Update coupon usage
                    coupon.used_count += 1
                    coupon.save()
                else:
                    raise serializers.ValidationError({'coupon_id': message})
            except Coupon.DoesNotExist:
                raise serializers.ValidationError({'coupon_id': 'Invalid coupon'})
        
        from .utils import calculate_order_totals
        
        # Calculate totals with platform fee (after coupon discount)
        subtotal_after_discount = subtotal - coupon_discount
        totals = calculate_order_totals(subtotal_after_discount, payment_method)
        
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