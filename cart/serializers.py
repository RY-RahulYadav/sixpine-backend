from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Product, ProductVariant


# Lightweight serializers to avoid heavy nested queries when returning cart data
class VariantMiniSerializer(serializers.ModelSerializer):
    color = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'title', 'price', 'stock_quantity', 'image', 'color', 'size', 'pattern', 'quality']

    def get_color(self, obj):
        if obj.color:
            return {'id': obj.color.id, 'name': obj.color.name, 'hex_code': obj.color.hex_code}
        return None


class ProductMiniSerializer(serializers.ModelSerializer):
    main_image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'main_image', 'price']

    def get_main_image(self, obj):
        # Prefer parent_main_image, then first active variant image, fallback to product main_image
        if getattr(obj, 'parent_main_image', None):
            return obj.parent_main_image
        first_variant = getattr(obj, 'variants', None)
        if first_variant is not None:
            # If prefetching was used, `variants` will be a queryset
            fv = obj.variants.filter(is_active=True).first()
            if fv:
                if fv.image:
                    return fv.image
                # try variant images if available
                try:
                    vi = fv.images.filter(is_active=True).order_by('sort_order').first()
                    if vi and vi.image:
                        return vi.image
                except Exception:
                    pass
        return obj.main_image

    def get_price(self, obj):
        fv = obj.variants.filter(is_active=True).first()
        if fv and fv.price:
            return float(fv.price)
        return None


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    variant = VariantMiniSerializer(read_only=True)
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
                
                # If product has variants but no variant_id provided, automatically select first active variant
                if product.variants.filter(is_active=True).exists() and not variant_id:
                    first_variant = product.variants.filter(is_active=True).first()
                    if first_variant:
                        attrs['variant_id'] = first_variant.id
                        variant_id = first_variant.id
                
                # If variant_id is provided (or auto-selected), validate it
                if variant_id:
                    try:
                        variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
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