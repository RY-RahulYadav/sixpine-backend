from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductListSerializer, ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'variant', 'variant_id', 'quantity', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['total_price', 'created_at', 'updated_at']

    def validate(self, attrs):
        from products.models import Product, ProductVariant
        
        if 'product_id' in attrs:
            try:
                product = Product.objects.get(id=attrs['product_id'])
                variant_id = attrs.get('variant_id')
                
                # If product has variants, variant_id must be provided
                if product.variants.exists() and not variant_id:
                    raise serializers.ValidationError("Variant is required for this product")
                
                # If variant_id is provided, validate it
                if variant_id:
                    try:
                        variant = ProductVariant.objects.get(id=variant_id, product=product)
                        quantity = attrs.get('quantity', 1)
                        if quantity > variant.stock_quantity:
                            raise serializers.ValidationError(
                                f"Only {variant.stock_quantity} items available in stock for this variant"
                            )
                    except ProductVariant.DoesNotExist:
                        raise serializers.ValidationError("Invalid variant for this product")
                    
            except Product.DoesNotExist:
                raise serializers.ValidationError("Product not found")
        return attrs


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    items_count = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_items', 'total_price', 'items_count', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']