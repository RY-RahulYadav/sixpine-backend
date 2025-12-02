from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.models import User, Vendor, Media, PackagingFeedback
from products.models import (
    Category, Subcategory, Color, Material, Product, ProductImage, 
    ProductVariant, ProductVariantImage, ProductSpecification, ProductFeature, 
    ProductOffer, Discount, ProductRecommendation, Coupon, ProductReview
)
from orders.models import Order, OrderItem, OrderStatusHistory, OrderNote
from accounts.models import ContactQuery, BulkOrder, DataRequest
from .models import GlobalSettings, AdminLog, HomePageContent, BulkOrderPageContent, FAQPageContent, Advertisement
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


# ==================== Global Settings Serializers ====================
class GlobalSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalSettings
        fields = ['id', 'key', 'value', 'description', 'created_at', 'updated_at']


# ==================== Dashboard Serializers ====================
class DashboardStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_net_profit = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    seller_net_profit = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    sixpine_profit = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    total_net_revenue = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    total_products = serializers.IntegerField()
    orders_placed_count = serializers.IntegerField()
    delivered_orders_count = serializers.IntegerField()
    cod_orders_count = serializers.IntegerField()
    online_payment_orders_count = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    recent_orders = serializers.ListField()
    top_selling_products = serializers.ListField()
    sales_by_day = serializers.ListField()


# ==================== User Serializers ====================
class AdminUserListSerializer(serializers.ModelSerializer):
    order_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'mobile',
            'is_active', 'is_staff', 'is_superuser', 'is_verified',
            'date_joined', 'last_login', 'order_count', 'total_spent'
        ]
    
    def get_order_count(self, obj):
        return obj.orders.count()
    
    def get_total_spent(self, obj):
        total = obj.orders.filter(payment_status='paid').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        return str(total)


class AdminUserDetailSerializer(serializers.ModelSerializer):
    order_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    recent_orders = serializers.SerializerMethodField()
    addresses_count = serializers.SerializerMethodField()
    interests = serializers.JSONField(default=list, allow_null=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'mobile',
            'is_active', 'is_staff', 'is_superuser', 'is_verified',
            'date_joined', 'last_login', 'order_count', 'total_spent',
            'recent_orders', 'addresses_count', 'interests', 'advertising_enabled',
            'whatsapp_enabled', 'whatsapp_order_updates', 'whatsapp_promotional', 'email_promotional'
        ]
    
    def to_representation(self, instance):
        """Ensure empty lists are returned instead of None"""
        data = super().to_representation(instance)
        if data.get('interests') is None:
            data['interests'] = []
        if data.get('advertising_enabled') is None:
            data['advertising_enabled'] = True
        if data.get('whatsapp_enabled') is None:
            data['whatsapp_enabled'] = True
        if data.get('whatsapp_order_updates') is None:
            data['whatsapp_order_updates'] = True
        if data.get('whatsapp_promotional') is None:
            data['whatsapp_promotional'] = True
        if data.get('email_promotional') is None:
            data['email_promotional'] = True
        return data
    
    def get_order_count(self, obj):
        return obj.orders.count()
    
    def get_total_spent(self, obj):
        total = obj.orders.filter(payment_status='paid').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        return str(total)
    
    def get_recent_orders(self, obj):
        orders = obj.orders.all()[:5]
        return [{
            'order_id': str(order.order_id),
            'status': order.status,
            'total_amount': str(order.total_amount),
            'created_at': order.created_at
        } for order in orders]
    
    def get_addresses_count(self, obj):
        return obj.addresses.count()


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'mobile',
            'password', 'is_active', 'is_staff', 'is_superuser', 'is_verified'
        ]
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'mobile',
            'is_active', 'is_staff', 'is_superuser', 'is_verified'
        ]
    
    def update(self, instance, validated_data):
        """Update user instance"""
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ==================== Category & Subcategory Serializers ====================
class AdminSubcategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Subcategory
        fields = [
            'id', 'name', 'slug', 'category', 'description', 'is_active',
            'sort_order', 'product_count', 'created_at', 'updated_at'
        ]
    
    def get_product_count(self, obj):
        return obj.products.count()


class AdminCategorySerializer(serializers.ModelSerializer):
    subcategories = AdminSubcategorySerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()
    subcategory_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'image', 'is_active',
            'sort_order', 'subcategories', 'product_count', 'subcategory_count',
            'created_at', 'updated_at'
        ]
    
    def get_product_count(self, obj):
        return obj.products.count()
    
    def get_subcategory_count(self, obj):
        return obj.subcategories.count()


# ==================== Color & Material Serializers ====================
class AdminColorSerializer(serializers.ModelSerializer):
    variant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Color
        fields = ['id', 'name', 'hex_code', 'is_active', 'variant_count', 'created_at']
    
    def get_variant_count(self, obj):
        return obj.variants.count()


class AdminMaterialSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Material
        fields = ['id', 'name', 'description', 'is_active', 'product_count', 'created_at']
    
    def get_product_count(self, obj):
        return obj.products.count()


# ==================== Product Serializers ====================
class AdminProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'sort_order', 'is_active']


class AdminProductVariantImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantImage
        fields = ['id', 'image', 'alt_text', 'sort_order', 'is_active']


class AdminProductVariantSerializer(serializers.ModelSerializer):
    color = AdminColorSerializer(read_only=True)
    color_id = serializers.IntegerField()
    images = AdminProductVariantImageSerializer(many=True, required=False)
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'title', 'color', 'color_id', 'size', 'pattern', 'quality',
            'price', 'old_price', 'discount_percentage', 'stock_quantity', 'is_in_stock',
            'image', 'images', 'is_active', 'created_at', 'updated_at'
        ]


class AdminProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['id', 'name', 'value', 'sort_order', 'is_active']


class AdminProductFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFeature
        fields = ['id', 'feature', 'sort_order', 'is_active']


class AdminProductOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOffer
        fields = [
            'id', 'title', 'description', 'discount_percentage',
            'discount_amount', 'is_active', 'valid_from', 'valid_until'
        ]


class AdminProductRecommendationSerializer(serializers.ModelSerializer):
    recommended_product_title = serializers.CharField(source='recommended_product.title', read_only=True)
    recommended_product_id = serializers.IntegerField(read_only=False)
    
    class Meta:
        model = ProductRecommendation
        fields = [
            'id', 'recommended_product_id', 'recommended_product_title',
            'recommendation_type', 'sort_order', 'is_active', 'created_at'
        ]
    
    def to_representation(self, instance):
        """Ensure recommended_product_id is included in the output"""
        data = super().to_representation(instance)
        # Django automatically provides recommended_product_id for ForeignKey fields
        # Make sure it's in the output
        if 'recommended_product_id' not in data or data['recommended_product_id'] is None:
            data['recommended_product_id'] = getattr(instance, 'recommended_product_id', None) or (instance.recommended_product.id if instance.recommended_product else None)
        return data


class AdminProductListSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField(read_only=True)
    subcategory = serializers.StringRelatedField(read_only=True)
    variant_count = serializers.SerializerMethodField()
    total_stock = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    
    # Price fields from first variant (for display purposes)
    price = serializers.SerializerMethodField()
    old_price = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    
    # Use first variant image for main_image
    main_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'sku', 'main_image', 'category', 'subcategory', 'price', 'old_price',
            'is_on_sale', 'discount_percentage', 'is_featured', 'is_active',
            'variant_count', 'total_stock', 'order_count', 'variants', 'created_at', 'updated_at'
        ]
    
    def get_main_image(self, obj):
        """Get image from first active variant"""
        first_variant = obj.variants.filter(is_active=True).first()
        if first_variant and first_variant.image:
            return first_variant.image
        # Fallback to product main_image if no variant image
        return obj.main_image
    
    def get_price(self, obj):
        """Get price from first active variant"""
        first_variant = obj.variants.filter(is_active=True).first()
        if first_variant and first_variant.price:
            return float(first_variant.price)
        return None
    
    def get_old_price(self, obj):
        """Get old_price from first active variant"""
        first_variant = obj.variants.filter(is_active=True).first()
        if first_variant and first_variant.old_price:
            return float(first_variant.old_price)
        return None
    
    def get_is_on_sale(self, obj):
        """Check if first variant is on sale"""
        first_variant = obj.variants.filter(is_active=True).first()
        if first_variant and first_variant.old_price and first_variant.price:
            return float(first_variant.old_price) > float(first_variant.price)
        return False
    
    def get_discount_percentage(self, obj):
        """Get discount percentage from first variant"""
        first_variant = obj.variants.filter(is_active=True).first()
        if first_variant and first_variant.discount_percentage:
            return first_variant.discount_percentage
        return 0
    
    def get_variant_count(self, obj):
        return obj.variants.count()
    
    def get_total_stock(self, obj):
        return sum(v.stock_quantity for v in obj.variants.all())
    
    def get_order_count(self, obj):
        return OrderItem.objects.filter(product=obj).aggregate(
            count=Count('id')
        )['count'] or 0
    
    def get_variants(self, obj):
        """Return basic variant info for display"""
        variants = obj.variants.filter(is_active=True)[:5]  # Limit to 5 variants for list view
        return [{
            'id': v.id,
            'title': v.title,
            'color': {
                'id': v.color.id,
                'name': v.color.name,
                'hex_code': v.color.hex_code
            },
            'size': v.size,
            'pattern': v.pattern,
            'quality': v.quality,
            'price': float(v.price) if v.price else None,
            'stock_quantity': v.stock_quantity,
            'is_in_stock': v.is_in_stock,
            'image': v.image
        } for v in variants]


class AdminProductDetailSerializer(serializers.ModelSerializer):
    category = AdminCategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=True, allow_null=False)
    subcategory = AdminSubcategorySerializer(read_only=True, allow_null=True)
    subcategory_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    material = AdminMaterialSerializer(read_only=True, allow_null=True)
    material_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    images = AdminProductImageSerializer(many=True, required=False)
    variants = AdminProductVariantSerializer(many=True, required=False)
    specifications = AdminProductSpecificationSerializer(many=True, required=False)
    features = AdminProductFeatureSerializer(many=True, required=False)
    offers = AdminProductOfferSerializer(many=True, required=False)
    recommendations = AdminProductRecommendationSerializer(many=True, required=False)
    
    # Note: price and old_price are not in Product model anymore - only in variants
    # These fields are kept for backward compatibility but will be read-only
    price = serializers.SerializerMethodField(read_only=True)
    old_price = serializers.SerializerMethodField(read_only=True)
    is_on_sale = serializers.SerializerMethodField(read_only=True)
    discount_percentage = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'sku', 'short_description', 'long_description',
            'main_image', 'category', 'category_id', 'subcategory', 'subcategory_id',
            'price', 'old_price', 'is_on_sale', 'discount_percentage',
            'brand', 'material', 'material_id', 'dimensions', 'weight', 'warranty',
            'assembly_required', 'estimated_delivery_days', 'screen_offer', 'user_guide', 'care_instructions',
            'meta_title', 'meta_description',
            'is_featured', 'is_active', 'images', 'variants', 'specifications',
            'features', 'offers', 'recommendations', 'average_rating', 'review_count',
            'created_at', 'updated_at'
        ]
    
    def get_price(self, obj):
        """Get price from first active variant"""
        first_variant = obj.variants.filter(is_active=True).first()
        if first_variant and first_variant.price:
            return float(first_variant.price)
        return None
    
    def get_old_price(self, obj):
        """Get old_price from first active variant"""
        first_variant = obj.variants.filter(is_active=True).first()
        if first_variant and first_variant.old_price:
            return float(first_variant.old_price)
        return None
    
    def get_is_on_sale(self, obj):
        """Check if first variant is on sale"""
        first_variant = obj.variants.filter(is_active=True).first()
        if first_variant and first_variant.old_price and first_variant.price:
            return float(first_variant.old_price) > float(first_variant.price)
        return False
    
    def get_discount_percentage(self, obj):
        """Get discount percentage from first variant"""
        first_variant = obj.variants.filter(is_active=True).first()
        if first_variant and first_variant.discount_percentage:
            return first_variant.discount_percentage
        return 0
    
    def create(self, validated_data):
        from django.db import transaction
        
        images_data = validated_data.pop('images', [])
        variants_data = validated_data.pop('variants', [])
        specifications_data = validated_data.pop('specifications', [])
        features_data = validated_data.pop('features', [])
        offers_data = validated_data.pop('offers', [])
        recommendations_data = validated_data.pop('recommendations', [])
        
        category_id = validated_data.pop('category_id', None)
        if category_id is None or category_id == 0:
            raise serializers.ValidationError({'category_id': 'Category is required'})
        
        # Validate that category exists
        from products.models import Category
        try:
            Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            raise serializers.ValidationError({'category_id': 'Invalid category selected'})
        
        subcategory_id = validated_data.pop('subcategory_id', None)
        material_id = validated_data.pop('material_id', None)
        
        # Use atomic transaction for all database operations
        with transaction.atomic():
            # Create product
            product = Product.objects.create(
                category_id=category_id,
                subcategory_id=subcategory_id,
                material_id=material_id,
                **validated_data
            )
            
            # Bulk create images for better performance
            if images_data:
                image_objects = [
                    ProductImage(product=product, **image_data)
                    for image_data in images_data
                ]
                ProductImage.objects.bulk_create(image_objects)
            
            # Create variants with images
            # Create variants individually to get IDs, but batch variant images
            variant_image_objects = []
            for variant_data in variants_data:
                variant_images = variant_data.pop('images', [])
                color_id = variant_data.pop('color_id')
                variant = ProductVariant.objects.create(
                    product=product,
                    color_id=color_id,
                    **variant_data
                )
                # Collect variant images for bulk creation
                if variant_images:
                    for variant_img_data in variant_images:
                        variant_image_objects.append(
                            ProductVariantImage(variant=variant, **variant_img_data)
                        )
            
            # Bulk create variant images for better performance
            if variant_image_objects:
                ProductVariantImage.objects.bulk_create(variant_image_objects)
            
            # Bulk create specifications
            if specifications_data:
                spec_objects = [
                    ProductSpecification(product=product, **spec_data)
                    for spec_data in specifications_data
                ]
                ProductSpecification.objects.bulk_create(spec_objects)
            
            # Bulk create features
            if features_data:
                feature_objects = [
                    ProductFeature(product=product, **feature_data)
                    for feature_data in features_data
                ]
                ProductFeature.objects.bulk_create(feature_objects)
            
            # Bulk create offers
            if offers_data:
                offer_objects = [
                    ProductOffer(product=product, **offer_data)
                    for offer_data in offers_data
                ]
                ProductOffer.objects.bulk_create(offer_objects)
            
            # Create recommendations (need individual handling due to get_or_create logic)
            if recommendations_data:
                recommendation_objects = []
                for rec_data in recommendations_data:
                    recommended_product_id = rec_data.pop('recommended_product_id')
                    recommendation_type = rec_data.get('recommendation_type', 'buy_with')
                    # Use get_or_create to avoid duplicate errors
                    rec, created = ProductRecommendation.objects.get_or_create(
                        product=product,
                        recommended_product_id=recommended_product_id,
                        recommendation_type=recommendation_type,
                        defaults=rec_data
                    )
                    if not created:
                        # Update existing recommendation
                        for attr, value in rec_data.items():
                            setattr(rec, attr, value)
                        rec.save()
        
        return product
    
    def update(self, instance, validated_data):
        from django.db import transaction
        
        images_data = validated_data.pop('images', None)
        variants_data = validated_data.pop('variants', None)
        specifications_data = validated_data.pop('specifications', None)
        features_data = validated_data.pop('features', None)
        offers_data = validated_data.pop('offers', None)
        recommendations_data = validated_data.pop('recommendations', None)
        
        category_id = validated_data.pop('category_id', None)
        subcategory_id = validated_data.pop('subcategory_id', None)
        material_id = validated_data.pop('material_id', None)
        
        # Use atomic transaction for all database operations
        with transaction.atomic():
            if category_id:
                instance.category_id = category_id
            if subcategory_id is not None:
                instance.subcategory_id = subcategory_id
            if material_id is not None:
                instance.material_id = material_id
            
            # Update product fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # Update images if provided - use bulk_create for better performance
            if images_data is not None:
                instance.images.all().delete()
                if images_data:
                    image_objects = [
                        ProductImage(product=instance, **image_data)
                        for image_data in images_data
                    ]
                    ProductImage.objects.bulk_create(image_objects)
        
        # Update variants if provided
        if variants_data is not None:
            # Keep existing variant IDs if provided, delete others
            existing_variant_ids = [v.get('id') for v in variants_data if v.get('id')]
            if existing_variant_ids:
                instance.variants.exclude(id__in=existing_variant_ids).delete()
            else:
                # If no IDs provided, delete all and recreate
                instance.variants.all().delete()
            
            for variant_data in variants_data:
                # Check if images key exists (not just pop default)
                variant_images = variant_data.pop('images') if 'images' in variant_data else None
                variant_id = variant_data.pop('id', None)
                color_id = variant_data.pop('color_id', None)
                
                if variant_id:
                    try:
                        variant = ProductVariant.objects.get(id=variant_id, product=instance)
                        for attr, value in variant_data.items():
                            setattr(variant, attr, value)
                        if color_id is not None:
                            variant.color_id = color_id
                        variant.save()
                        
                        # Update variant images only if provided (empty list means delete all)
                        if variant_images is not None:
                            variant.images.all().delete()
                            # Only create images if list is not empty - use bulk_create
                            if variant_images:
                                variant_image_objects = [
                                    ProductVariantImage(variant=variant, **variant_img_data)
                                    for variant_img_data in variant_images
                                ]
                                ProductVariantImage.objects.bulk_create(variant_image_objects)
                    except ProductVariant.DoesNotExist:
                        # If variant doesn't exist, create new one
                        if color_id is None:
                            raise serializers.ValidationError({'variants': 'color_id is required for new variants'})
                        variant = ProductVariant.objects.create(
                            product=instance,
                            color_id=color_id,
                            **variant_data
                        )
                        if variant_images:
                            variant_image_objects = [
                                ProductVariantImage(variant=variant, **variant_img_data)
                                for variant_img_data in variant_images
                            ]
                            ProductVariantImage.objects.bulk_create(variant_image_objects)
                else:
                    # New variant without ID
                    if color_id is None:
                        raise serializers.ValidationError({'variants': 'color_id is required for new variants'})
                    variant = ProductVariant.objects.create(
                        product=instance,
                        color_id=color_id,
                        **variant_data
                    )
                    if variant_images:
                        variant_image_objects = [
                            ProductVariantImage(variant=variant, **variant_img_data)
                            for variant_img_data in variant_images
                        ]
                        ProductVariantImage.objects.bulk_create(variant_image_objects)
        
            # Update specifications if provided - use bulk_create for better performance
            if specifications_data is not None:
                instance.specifications.all().delete()
                if specifications_data:
                    spec_objects = [
                        ProductSpecification(product=instance, **spec_data)
                        for spec_data in specifications_data
                    ]
                    ProductSpecification.objects.bulk_create(spec_objects)
            
            # Update features if provided - use bulk_create for better performance
            if features_data is not None:
                instance.features.all().delete()
                if features_data:
                    feature_objects = [
                        ProductFeature(product=instance, **feature_data)
                        for feature_data in features_data
                    ]
                    ProductFeature.objects.bulk_create(feature_objects)
            
            # Update offers if provided - use bulk_create for better performance
            if offers_data is not None:
                instance.offers.all().delete()
                if offers_data:
                    offer_objects = [
                        ProductOffer(product=instance, **offer_data)
                        for offer_data in offers_data
                    ]
                    ProductOffer.objects.bulk_create(offer_objects)
        
        # Update recommendations if provided
        if recommendations_data is not None:
            # Keep existing recommendation IDs if provided, delete others
            existing_rec_ids = [r.get('id') for r in recommendations_data if r.get('id')]
            if existing_rec_ids:
                instance.recommendations.exclude(id__in=existing_rec_ids).delete()
            else:
                # If no IDs provided, delete all and recreate
                instance.recommendations.all().delete()
            
            for rec_data in recommendations_data:
                recommended_product_id = rec_data.pop('recommended_product_id')
                rec_id = rec_data.pop('id', None)
                recommendation_type = rec_data.get('recommendation_type', 'buy_with')
                
                if rec_id:
                    try:
                        rec = ProductRecommendation.objects.get(id=rec_id, product=instance)
                        for attr, value in rec_data.items():
                            setattr(rec, attr, value)
                        rec.recommended_product_id = recommended_product_id
                        rec.save()
                    except ProductRecommendation.DoesNotExist:
                        # If recommendation doesn't exist, use get_or_create to avoid duplicates
                        rec, created = ProductRecommendation.objects.get_or_create(
                            product=instance,
                            recommended_product_id=recommended_product_id,
                            recommendation_type=recommendation_type,
                            defaults=rec_data
                        )
                        if not created:
                            # Update existing recommendation
                            for attr, value in rec_data.items():
                                setattr(rec, attr, value)
                            rec.save()
                else:
                    # New recommendation without ID - use get_or_create to avoid duplicates
                    rec, created = ProductRecommendation.objects.get_or_create(
                        product=instance,
                        recommended_product_id=recommended_product_id,
                        recommendation_type=recommendation_type,
                        defaults=rec_data
                    )
                    if not created:
                        # Update existing recommendation
                        for attr, value in rec_data.items():
                            setattr(rec, attr, value)
                        rec.save()
        
        return instance


# ==================== Order Serializers ====================
class AdminOrderItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    product_id = serializers.IntegerField(read_only=True)
    variant_info = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_id', 'variant', 'variant_color',
            'variant_size', 'variant_pattern', 'quantity', 'price', 'total_price', 'variant_info'
        ]
    
    def get_product(self, obj):
        if obj.product:
            # Handle main_image - it might be a string (URL) or a file field
            main_image = None
            if obj.product.main_image:
                if isinstance(obj.product.main_image, str):
                    # It's already a URL string
                    main_image = obj.product.main_image
                elif hasattr(obj.product.main_image, 'url'):
                    # It's a file field
                    main_image = obj.product.main_image.url
                else:
                    # Try to get the URL from the field
                    try:
                        main_image = obj.product.main_image.url
                    except (AttributeError, ValueError):
                        main_image = str(obj.product.main_image) if obj.product.main_image else None
            
            return {
                'id': obj.product.id,
                'title': obj.product.title,
                'slug': obj.product.slug,
                'main_image': main_image
            }
        return None
    
    def get_variant_info(self, obj):
        if obj.variant:
            color = obj.variant.color.name if obj.variant.color else ''
            size = obj.variant.size or ''
            pattern = obj.variant.pattern or ''
            quality = obj.variant.quality or ''
            parts = [p for p in [color, size, pattern, quality] if p]
            return ' - '.join(parts) if parts else ''
        parts = [p for p in [obj.variant_color, obj.variant_size, obj.variant_pattern] if p]
        return ' - '.join(parts) if parts else ''


class AdminOrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    items_count = serializers.ReadOnlyField()
    order_value = serializers.SerializerMethodField()
    net_profit = serializers.SerializerMethodField()
    vendor_profit = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'customer_name', 'customer_email', 'status',
            'payment_status', 'payment_method', 'items_count',
            'order_value', 'net_profit', 'vendor_profit',
            'created_at', 'estimated_delivery'
        ]
    
    def get_customer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    def get_customer_email(self, obj):
        return obj.user.email
    
    def get_order_value(self, obj):
        """Get total order value (total_amount including tax that customer paid)"""
        from decimal import Decimal
        # Return the total_amount which includes tax, platform fee, shipping, etc.
        return str(obj.total_amount or Decimal('0.00'))
    
    def get_net_profit(self, obj):
        """Get net profit (tax + platform fee) - only for delivered orders"""
        from decimal import Decimal
        if obj.status != 'delivered':
            return '0.00'
        net_profit = (obj.tax_amount or Decimal('0.00')) + (obj.platform_fee or Decimal('0.00'))
        return str(net_profit)
    
    def get_vendor_profit(self, obj):
        """Get vendor profit (order value - net profit) - only for delivered orders"""
        from orders.models import OrderItem
        from django.db.models import Sum, F, DecimalField
        from decimal import Decimal
        if obj.status != 'delivered':
            return '0.00'
        # Calculate order value
        order_value = OrderItem.objects.filter(order=obj).aggregate(
            total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'] or Decimal('0.00')
        # Calculate net profit
        net_profit = (obj.tax_amount or Decimal('0.00')) + (obj.platform_fee or Decimal('0.00'))
        # Vendor profit = order value - net profit
        vendor_profit = order_value - net_profit
        return str(max(vendor_profit, Decimal('0.00')))


class SellerOrderListSerializer(serializers.ModelSerializer):
    """Serializer for seller orders with vendor-specific calculations"""
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    items_count = serializers.ReadOnlyField()
    vendor_order_value = serializers.SerializerMethodField()
    vendor_net_revenue = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'customer_name', 'customer_email', 'status',
            'payment_status', 'payment_method', 'items_count',
            'vendor_order_value', 'vendor_net_revenue',
            'created_at', 'estimated_delivery'
        ]
    
    def get_customer_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    def get_customer_email(self, obj):
        return obj.user.email
    
    def get_vendor_order_value(self, obj):
        """Get vendor's share of total order value (including tax)"""
        from django.db.models import Sum, F, DecimalField
        from decimal import Decimal
        vendor = self.context.get('vendor')
        if not vendor:
            return '0.00'
        
        vendor_items = obj.items.filter(vendor=vendor)
        vendor_items_subtotal = vendor_items.aggregate(
            total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'] or Decimal('0.00')
        
        # Calculate vendor's share of total amount (proportional to their items)
        if obj.subtotal > 0:
            vendor_share_ratio = vendor_items_subtotal / obj.subtotal
            vendor_order_value = obj.total_amount * vendor_share_ratio
        else:
            vendor_order_value = vendor_items_subtotal
        
        return str(vendor_order_value)
    
    def get_vendor_net_revenue(self, obj):
        """Calculate vendor's net revenue after platform fees and taxes"""
        from django.db.models import Sum, F, DecimalField
        from decimal import Decimal
        from admin_api.models import GlobalSettings
        
        vendor = self.context.get('vendor')
        if not vendor:
            return '0.00'
        
        # Get vendor's items in this order
        vendor_items = obj.items.filter(vendor=vendor)
        vendor_order_value = vendor_items.aggregate(
            total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'] or Decimal('0.00')
        
        if vendor_order_value == 0:
            return '0.00'
        
        # Calculate vendor's share of platform fee
        order_total_items = obj.items.aggregate(
            total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'] or Decimal('0.00')
        
        vendor_platform_fee = Decimal('0.00')
        vendor_tax = Decimal('0.00')
        
        if order_total_items > 0:
            vendor_platform_fee = (vendor_order_value / order_total_items) * (obj.platform_fee or Decimal('0.00'))
            order_subtotal = obj.subtotal
            if order_subtotal > 0:
                vendor_tax = (vendor_order_value / order_subtotal) * (obj.tax_amount or Decimal('0.00'))
            else:
                tax_rate = Decimal(str(GlobalSettings.get_setting('tax_rate', '5.00')))
                vendor_tax = (vendor_order_value * tax_rate) / Decimal('100.00')
        
        net_revenue = vendor_order_value - vendor_platform_fee - vendor_tax
        return str(max(net_revenue, Decimal('0.00')))


class AdminOrderDetailSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()  # Keep for backward compatibility
    items = AdminOrderItemSerializer(many=True, read_only=True)
    order_number = serializers.CharField(source='order_id', read_only=True)
    shipping_address = serializers.SerializerMethodField()
    billing_address = serializers.SerializerMethodField()
    status_history = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    items_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'order_number', 'user', 'customer', 'status', 'payment_status', 'payment_method',
            'subtotal', 'coupon', 'coupon_discount', 'shipping_cost', 'platform_fee', 'tax_amount', 'total_amount',
            'shipping_address', 'billing_address', 'tracking_number', 'estimated_delivery', 'delivered_at',
            'order_notes', 'items', 'items_count', 'status_history', 'notes',
            'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature',
            'created_at', 'updated_at'
        ]
    
    def to_representation(self, instance):
        """Add computed fields for backward compatibility"""
        data = super().to_representation(instance)
        # Add 'tax' as alias for 'tax_amount' for frontend compatibility
        data['tax'] = data.get('tax_amount', 0)
        # Add 'total' as alias for 'total_amount' for frontend compatibility
        data['total'] = data.get('total_amount', 0)
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
        # Use coupon_discount from model, fallback to calculated if not present
        coupon_discount = float(data.get('coupon_discount', 0))
        if coupon_discount == 0:
            # Calculate discount if needed (subtotal + tax + platform_fee + shipping - total_amount)
            subtotal = float(data.get('subtotal', 0))
            tax = float(data.get('tax_amount', 0))
            platform_fee = float(data.get('platform_fee', 0))
            shipping = float(data.get('shipping_cost', 0))
            total = float(data.get('total_amount', 0))
            calculated_total = subtotal + tax + platform_fee + shipping
            discount_amount = max(0, calculated_total - total)
            coupon_discount = discount_amount if discount_amount > 0 else 0
        data['coupon_discount'] = coupon_discount
        data['discount'] = coupon_discount  # For backward compatibility
        return data
    
    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'full_name': obj.user.get_full_name(),
            'mobile': getattr(obj.user, 'mobile', None)
        }
    
    def get_customer(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'full_name': obj.user.get_full_name(),
            'mobile': getattr(obj.user, 'mobile', None)
        }
    
    def get_billing_address(self, obj):
        if hasattr(obj, 'billing_address') and obj.billing_address:
            addr = obj.billing_address
            return {
                'id': addr.id,
                'full_name': getattr(addr, 'full_name', ''),
                'phone': getattr(addr, 'phone', ''),
                'address_line1': getattr(addr, 'address_line1', getattr(addr, 'street_address', '')),
                'address_line2': getattr(addr, 'address_line2', ''),
                'city': addr.city,
                'state': addr.state,
                'postal_code': getattr(addr, 'postal_code', getattr(addr, 'zip_code', '')),
                'country': addr.country
            }
        return None
    
    def get_shipping_address(self, obj):
        addr = obj.shipping_address
        return {
            'id': addr.id,
            'full_name': addr.full_name,
            'phone': addr.phone,
            'address_line1': getattr(addr, 'address_line1', addr.street_address),
            'address_line2': getattr(addr, 'address_line2', ''),
            'street_address': addr.street_address,
            'city': addr.city,
            'state': addr.state,
            'postal_code': addr.postal_code,
            'country': addr.country
        }
    
    def get_status_history(self, obj):
        return [{
            'status': h.status,
            'notes': h.notes,
            'created_at': h.created_at,
            'created_by': h.created_by.username if h.created_by else None
        } for h in obj.status_history.all()]
    
    def get_notes(self, obj):
        return [{
            'id': n.id,
            'content': n.content,
            'created_at': n.created_at,
            'created_by': n.created_by.username if n.created_by else None
        } for n in obj.notes.all()]


# ==================== Discount Serializers ====================
class AdminDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['id', 'percentage', 'label', 'is_active', 'created_at']


# ==================== Payment & Charges Serializers ====================
class PaymentChargeSerializer(serializers.Serializer):
    """Serializer for payment charges configuration"""
    # Platform fees per payment method (percentage)
    platform_fee_upi = serializers.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='Platform fee percentage for UPI payments (Razorpay: 0%)')
    platform_fee_card = serializers.DecimalField(max_digits=5, decimal_places=2, default=2.36, help_text='Platform fee percentage for Credit/Debit Card payments (Razorpay: 2.36% including GST)')
    platform_fee_netbanking = serializers.DecimalField(max_digits=5, decimal_places=2, default=2.36, help_text='Platform fee percentage for Net Banking payments (Razorpay: 2.36% including GST)')
    platform_fee_cod = serializers.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='Platform fee percentage for COD payments (Cash on Delivery: 0%)')
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    razorpay_enabled = serializers.BooleanField()
    cod_enabled = serializers.BooleanField()


# ==================== Brand/Vendor Serializers ====================
class AdminBrandSerializer(serializers.ModelSerializer):
    """Serializer for brand/vendor listing in admin panel"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    total_products = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    total_order_value = serializers.SerializerMethodField()
    total_net_profit = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'business_name', 'business_email', 'business_phone',
            'brand_name', 'status', 'status_display', 'is_verified',
            'created_at', 'updated_at',
            'total_products', 'total_orders', 'total_order_value', 'total_net_profit'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'total_products', 'total_orders', 'total_order_value', 'total_net_profit']
    
    def get_user_name(self, obj):
        """Get user's full name"""
        if obj.user:
            full_name = f"{obj.user.first_name or ''} {obj.user.last_name or ''}".strip()
            return full_name or obj.user.username or obj.user.email
        return 'N/A'
    
    def get_total_products(self, obj):
        """Get total products count for this vendor"""
        from products.models import Product
        return Product.objects.filter(vendor=obj).count()
    
    def get_total_orders(self, obj):
        """Get total orders count for this vendor"""
        from orders.models import Order, OrderItem
        return Order.objects.filter(items__vendor=obj).distinct().count()
    
    def get_total_order_value(self, obj):
        """Get total order value (sum of total_amount including tax for orders containing vendor's products)"""
        from orders.models import Order, OrderItem
        from django.db.models import Sum, F, DecimalField
        from decimal import Decimal
        
        # Get all orders containing vendor's products
        vendor_orders = Order.objects.filter(items__vendor=obj).distinct()
        
        total_order_value = Decimal('0.00')
        for order in vendor_orders:
            # Get vendor's items in this order
            vendor_items = order.items.filter(vendor=obj)
            vendor_items_subtotal = vendor_items.aggregate(
                total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'] or Decimal('0.00')
            
            # Calculate vendor's share of total amount (proportional to their items)
            if order.subtotal > 0:
                vendor_share_ratio = vendor_items_subtotal / order.subtotal
                vendor_share_of_total = order.total_amount * vendor_share_ratio
                total_order_value += vendor_share_of_total
            else:
                # Fallback: if subtotal is 0, use vendor items value
                total_order_value += vendor_items_subtotal
        
        return str(total_order_value)
    
    def get_total_net_profit(self, obj):
        """Get total net profit (tax + platform fee) for this vendor's delivered orders only"""
        from orders.models import OrderItem, Order
        from django.db.models import Sum, F, DecimalField
        from decimal import Decimal
        from admin_api.models import GlobalSettings
        
        # Get delivered order items for this vendor only
        vendor_order_items = OrderItem.objects.filter(vendor=obj, order__status='delivered').select_related('order')
        
        total_platform_fees = Decimal('0.00')
        total_taxes = Decimal('0.00')
        tax_rate = Decimal(str(GlobalSettings.get_setting('tax_rate', '5.00')))
        
        # Calculate for each delivered order item
        for order_item in vendor_order_items:
            item_subtotal = order_item.price * order_item.quantity
            order = order_item.order
            
            # Calculate vendor's share of platform fee
            order_total_items = order.items.aggregate(
                total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
            )['total'] or Decimal('0.00')
            
            if order_total_items > 0:
                # Vendor's share of platform fee = (vendor_items_value / order_total) * platform_fee
                vendor_share_platform_fee = (item_subtotal / order_total_items) * (order.platform_fee or Decimal('0.00'))
                total_platform_fees += vendor_share_platform_fee
                
                # Tax is calculated on subtotal (before platform fee)
                order_subtotal = order.subtotal
                if order_subtotal > 0:
                    vendor_share_tax = (item_subtotal / order_subtotal) * (order.tax_amount or Decimal('0.00'))
                    total_taxes += vendor_share_tax
                else:
                    # Fallback: calculate tax directly on vendor's item
                    vendor_share_tax = (item_subtotal * tax_rate) / Decimal('100.00')
                    total_taxes += vendor_share_tax
        
        # Net profit = tax + platform fee
        net_profit = total_taxes + total_platform_fees
        return str(net_profit)


class AdminBrandDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for brand/vendor with all information"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_mobile = serializers.CharField(source='user.mobile', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    total_products = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    total_order_value = serializers.SerializerMethodField()
    total_net_profit = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'user', 'user_email', 'user_name', 'user_first_name', 'user_last_name',
            'user_mobile', 'user_username',
            'business_name', 'business_email', 'business_phone', 'business_address',
            'city', 'state', 'pincode', 'country',
            'gst_number', 'pan_number', 'business_type',
            'brand_name', 'status', 'status_display', 'is_verified',
            'commission_percentage', 'low_stock_threshold',
            # Payment details
            'account_holder_name', 'account_number', 'ifsc_code',
            'bank_name', 'branch_name', 'upi_id',
            # Shipment details
            'shipment_address', 'shipment_city', 'shipment_state',
            'shipment_pincode', 'shipment_country',
            'shipment_latitude', 'shipment_longitude',
            'created_at', 'updated_at', 'approved_at',
            'total_products', 'total_orders', 'total_order_value', 'total_net_profit'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'total_products', 'total_orders', 'total_order_value', 'total_net_profit']
    
    def get_user_name(self, obj):
        """Get user's full name"""
        if obj.user:
            full_name = f"{obj.user.first_name or ''} {obj.user.last_name or ''}".strip()
            return full_name or obj.user.username or obj.user.email
        return 'N/A'
    
    def get_total_products(self, obj):
        """Get total products count for this vendor"""
        from products.models import Product
        return Product.objects.filter(vendor=obj).count()
    
    def get_total_orders(self, obj):
        """Get total orders count for this vendor"""
        from orders.models import Order, OrderItem
        return Order.objects.filter(items__vendor=obj).distinct().count()
    
    def get_total_order_value(self, obj):
        """Get total order value (sum of total_amount including tax for orders containing vendor's products)"""
        from orders.models import Order, OrderItem
        from django.db.models import Sum, F, DecimalField
        from decimal import Decimal
        
        # Get all orders containing vendor's products
        vendor_orders = Order.objects.filter(items__vendor=obj).distinct()
        
        total_order_value = Decimal('0.00')
        for order in vendor_orders:
            # Get vendor's items in this order
            vendor_items = order.items.filter(vendor=obj)
            vendor_items_subtotal = vendor_items.aggregate(
                total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
            )['total'] or Decimal('0.00')
            
            # Calculate vendor's share of total amount (proportional to their items)
            if order.subtotal > 0:
                vendor_share_ratio = vendor_items_subtotal / order.subtotal
                vendor_share_of_total = order.total_amount * vendor_share_ratio
                total_order_value += vendor_share_of_total
            else:
                # Fallback: if subtotal is 0, use vendor items value
                total_order_value += vendor_items_subtotal
        
        return str(total_order_value)
    
    def get_total_net_profit(self, obj):
        """Get total net profit (tax + platform fee) for this vendor's delivered orders only"""
        from orders.models import OrderItem, Order
        from django.db.models import Sum, F, DecimalField
        from decimal import Decimal
        from admin_api.models import GlobalSettings
        
        # Get delivered order items for this vendor only
        vendor_order_items = OrderItem.objects.filter(vendor=obj, order__status='delivered').select_related('order')
        
        total_platform_fees = Decimal('0.00')
        total_taxes = Decimal('0.00')
        tax_rate = Decimal(str(GlobalSettings.get_setting('tax_rate', '5.00')))
        
        # Calculate for each delivered order item
        for order_item in vendor_order_items:
            item_subtotal = order_item.price * order_item.quantity
            order = order_item.order
            
            # Calculate vendor's share of platform fee
            order_total_items = order.items.aggregate(
                total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
            )['total'] or Decimal('0.00')
            
            if order_total_items > 0:
                # Vendor's share of platform fee = (vendor_items_value / order_total) * platform_fee
                vendor_share_platform_fee = (item_subtotal / order_total_items) * (order.platform_fee or Decimal('0.00'))
                total_platform_fees += vendor_share_platform_fee
                
                # Tax is calculated on subtotal (before platform fee)
                order_subtotal = order.subtotal
                if order_subtotal > 0:
                    vendor_share_tax = (item_subtotal / order_subtotal) * (order.tax_amount or Decimal('0.00'))
                    total_taxes += vendor_share_tax
                else:
                    # Fallback: calculate tax directly on vendor's item
                    vendor_share_tax = (item_subtotal * tax_rate) / Decimal('100.00')
                    total_taxes += vendor_share_tax
        
        # Net profit = tax + platform fee
        net_profit = total_taxes + total_platform_fees
        return str(net_profit)


# ==================== Contact Query Serializers ====================
class AdminContactQuerySerializer(serializers.ModelSerializer):
    """Serializer for contact queries in admin panel"""
    class Meta:
        model = ContactQuery
        fields = [
            'id', 'full_name', 'pincode', 'phone_number', 'email', 'message',
            'status', 'admin_notes', 'created_at', 'updated_at', 'resolved_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'resolved_at']


# ==================== Bulk Order Serializers ====================
class AdminBulkOrderSerializer(serializers.ModelSerializer):
    """Serializer for bulk orders in admin panel"""
    assigned_to_name = serializers.SerializerMethodField()
    assigned_to_email = serializers.SerializerMethodField()
    
    class Meta:
        model = BulkOrder
        fields = [
            'id', 'company_name', 'contact_person', 'email', 'phone_number',
            'address', 'city', 'state', 'pincode', 'country', 'project_type',
            'estimated_quantity', 'estimated_budget', 'delivery_date',
            'special_requirements', 'status', 'admin_notes', 'quoted_price',
            'assigned_to', 'assigned_to_name', 'assigned_to_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip() or obj.assigned_to.email
        return None
    
    def get_assigned_to_email(self, obj):
        return obj.assigned_to.email if obj.assigned_to else None


# ==================== Admin Log Serializers ====================
class AdminLogSerializer(serializers.ModelSerializer):
    """Serializer for admin logs"""
    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminLog
        fields = [
            'id', 'user', 'user_email', 'user_name', 'action_type',
            'model_name', 'object_id', 'object_repr', 'details',
            'ip_address', 'user_agent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_user_email(self, obj):
        return obj.user.email if obj.user else None
    
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return None


# ==================== Coupon Serializers ====================
class AdminCouponSerializer(serializers.ModelSerializer):
    is_valid_now = serializers.SerializerMethodField()
    remaining_uses = serializers.SerializerMethodField()
    vendor_name = serializers.SerializerMethodField()
    coupon_type_display = serializers.CharField(source='get_coupon_type_display', read_only=True)
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'coupon_type', 'coupon_type_display', 'vendor', 'vendor_name', 'description', 
            'discount_type', 'discount_value', 'min_order_amount', 'max_discount_amount', 
            'valid_from', 'valid_until', 'is_active', 'usage_limit', 'used_count', 
            'one_time_use_per_user', 'is_valid_now', 'remaining_uses', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'used_count']
    
    def get_vendor_name(self, obj):
        return obj.vendor.brand_name if obj.vendor else None
    
    def get_is_valid_now(self, obj):
        return obj.is_valid()
    
    def get_remaining_uses(self, obj):
        if obj.usage_limit:
            return obj.usage_limit - obj.used_count
        return None
    
    def validate_coupon_type(self, value):
        """Prevent admins from creating 'common' coupons that reduce seller product prices"""
        if value == 'common':
            raise serializers.ValidationError(
                "Admin cannot create 'common' coupons that reduce prices of other sellers' products. "
                "Use 'sixpine' for Sixpine products only or 'seller' for platform fee & tax only."
            )
        return value


# ==================== Home Page Content Serializers ====================
class HomePageContentSerializer(serializers.ModelSerializer):
    """Serializer for home page content sections"""
    class Meta:
        model = HomePageContent
        fields = [
            'id', 'section_key', 'section_name', 'content',
            'is_active', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_content(self, value):
        """Validate that content is a dict"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Content must be a JSON object")
        return value


class BulkOrderPageContentSerializer(serializers.ModelSerializer):
    """Serializer for bulk order page content sections"""
    class Meta:
        model = BulkOrderPageContent
        fields = [
            'id', 'section_key', 'section_name', 'content',
            'is_active', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_content(self, value):
        """Validate that content is a dict"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Content must be a JSON object")
        return value


class FAQPageContentSerializer(serializers.ModelSerializer):
    """Serializer for FAQ page content sections"""
    class Meta:
        model = FAQPageContent
        fields = [
            'id', 'section_key', 'section_name', 'content',
            'is_active', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_content(self, value):
        """Validate that content is a dict"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Content must be a JSON object")
        return value


class AdvertisementSerializer(serializers.ModelSerializer):
    """Serializer for advertisements"""
    is_valid_now = serializers.SerializerMethodField()
    
    class Meta:
        model = Advertisement
        fields = [
            'id', 'title', 'description', 'image', 'button_text', 'button_link',
            'discount_percentage', 'is_active', 'display_order',
            'valid_from', 'valid_until', 'is_valid_now', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_valid_now(self, obj):
        """Check if advertisement is currently valid"""
        return obj.is_valid()


class AdminDataRequestSerializer(serializers.ModelSerializer):
    """Serializer for data requests in admin panel"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = DataRequest
        fields = [
            'id', 'user', 'user_email', 'user_name', 'request_type', 'request_type_display',
            'status', 'status_display', 'file_path', 'requested_at', 'approved_at',
            'approved_by', 'approved_by_email', 'completed_at', 'admin_notes'
        ]
        read_only_fields = ['id', 'requested_at', 'approved_at', 'approved_by', 'completed_at']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


# ==================== Media Serializers ====================
class AdminMediaSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    uploaded_by_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Media
        fields = [
            'id', 'cloudinary_url', 'cloudinary_public_id', 'file_name', 
            'file_size', 'mime_type', 'alt_text', 'description',
            'uploaded_by_user', 'uploaded_by_vendor', 'uploaded_by_name',
            'uploaded_by_type', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by_user:
            return obj.uploaded_by_user.email
        elif obj.uploaded_by_vendor:
            return obj.uploaded_by_vendor.brand_name or obj.uploaded_by_vendor.business_name
        return 'Unknown'
    
    def get_uploaded_by_type(self, obj):
        if obj.uploaded_by_user:
            return 'admin'
        elif obj.uploaded_by_vendor:
            return 'seller'
        return 'unknown'


# ==================== Packaging Feedback Serializers ====================
class AdminPackagingFeedbackSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    feedback_type_display = serializers.CharField(source='get_feedback_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewed_by_email = serializers.EmailField(source='reviewed_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = PackagingFeedback
        fields = [
            'id', 'user', 'user_email', 'user_name', 'feedback_type', 'feedback_type_display',
            'rating', 'was_helpful', 'message', 'order_id', 'product_id',
            'email', 'name', 'status', 'status_display', 'admin_notes',
            'reviewed_by', 'reviewed_by_email', 'reviewed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'reviewed_at']
    
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
        return obj.name or 'Anonymous'


# ==================== Product Review Serializers ====================
class AdminProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for product reviews in admin panel"""
    user_name = serializers.SerializerMethodField()
    user_email = serializers.CharField(source='user.email', read_only=True)
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    vendor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'product', 'product_title', 'product_slug', 'user', 'user_name', 
            'user_email', 'rating', 'title', 'comment', 'is_verified_purchase', 
            'is_approved', 'created_at', 'updated_at', 'vendor_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
        return 'Anonymous'
    
    def get_vendor_name(self, obj):
        if obj.product and obj.product.vendor:
            return obj.product.vendor.business_name or obj.product.vendor.brand_name or 'N/A'
        return 'N/A'

