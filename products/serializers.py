from rest_framework import serializers
from django.db.models import Q
from .models import (
    Category, Subcategory, Color, Material, Product, ProductImage, ProductVariant,
    ProductVariantImage, ProductReview, ProductRecommendation, ProductSpecification, 
    ProductFeature, ProductAboutItem, ProductOffer, BrowsingHistory, Wishlist,
    VariantMeasurementSpec, VariantStyleSpec, VariantFeature, VariantUserGuide, VariantItemDetail
)


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'name', 'hex_code']


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ['id', 'name', 'description']


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'slug', 'description']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'subcategories']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'sort_order']


class ProductVariantImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantImage
        fields = ['id', 'image', 'alt_text', 'sort_order']


class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['id', 'name', 'value', 'sort_order']


class VariantMeasurementSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantMeasurementSpec
        fields = ['id', 'name', 'value', 'sort_order']


class VariantStyleSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantStyleSpec
        fields = ['id', 'name', 'value', 'sort_order']


class VariantFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantFeature
        fields = ['id', 'name', 'value', 'sort_order']


class VariantUserGuideSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantUserGuide
        fields = ['id', 'name', 'value', 'sort_order']


class VariantItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantItemDetail
        fields = ['id', 'name', 'value', 'sort_order']


class ProductVariantSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    color_id = serializers.IntegerField(write_only=True)
    images = ProductVariantImageSerializer(many=True, read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    measurement_specs = VariantMeasurementSpecSerializer(many=True, read_only=True)
    style_specs = VariantStyleSpecSerializer(many=True, read_only=True)
    features = VariantFeatureSerializer(many=True, read_only=True)
    user_guide = VariantUserGuideSerializer(many=True, read_only=True)
    item_details = VariantItemDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'title', 'color', 'color_id', 'size', 'pattern', 'quality', 'price', 'old_price',
            'discount_percentage', 'stock_quantity', 'is_in_stock', 'image', 'images', 'specifications',
            'measurement_specs', 'style_specs', 'features', 'user_guide', 'item_details'
        ]


class ProductFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFeature
        fields = ['id', 'feature', 'sort_order']


class ProductAboutItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAboutItem
        fields = ['id', 'item', 'sort_order']


class ProductOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOffer
        fields = [
            'id', 'title', 'description', 'discount_percentage', 
            'discount_amount', 'valid_from', 'valid_until'
        ]


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for product listing pages"""
    category = CategorySerializer(read_only=True)
    subcategory = SubcategorySerializer(read_only=True)
    material = MaterialSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    
    # Available colors for filtering
    available_colors = serializers.SerializerMethodField()
    
    # Variant count for frontend
    variant_count = serializers.SerializerMethodField()
    
    # Color count for frontend
    color_count = serializers.SerializerMethodField()
    
    # Real review data
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
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
            'id', 'title', 'slug', 'short_description', 'main_image',
            'price', 'old_price', 'is_on_sale', 'discount_percentage',
            'average_rating', 'review_count', 'category', 'subcategory',
            'brand', 'material', 'images', 'variants', 'available_colors',
            'variant_count', 'color_count', 'is_featured', 'created_at'
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
    
    def get_available_colors(self, obj):
        """Get unique colors available for this product"""
        colors = obj.variants.filter(is_active=True).values_list('color__name', flat=True).distinct()
        return list(colors)
    
    def get_variant_count(self, obj):
        """Get count of active variants for this product"""
        return obj.variants.filter(is_active=True).count()
    
    def get_color_count(self, obj):
        """Get distinct color count from active variants"""
        return obj.variants.filter(is_active=True).values('color').distinct().count()
    
    def get_review_count(self, obj):
        """Get actual review count from database"""
        return obj.reviews.filter(is_approved=True).count()
    
    def get_average_rating(self, obj):
        """Get actual average rating from database"""
        from django.db.models import Avg
        avg_rating = obj.reviews.filter(is_approved=True).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating']
        return round(float(avg_rating), 1) if avg_rating else 0.0


class ProductDetailSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for product detail pages"""
    category = CategorySerializer(read_only=True)
    subcategory = SubcategorySerializer(read_only=True)
    material = MaterialSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    features = ProductFeatureSerializer(many=True, read_only=True)
    about_items = ProductAboutItemSerializer(many=True, read_only=True)
    offers = ProductOfferSerializer(many=True, read_only=True)
    
    # Recommendation arrays
    buy_with_products = serializers.SerializerMethodField()
    inspired_products = serializers.SerializerMethodField()
    frequently_viewed_products = serializers.SerializerMethodField()
    similar_products = serializers.SerializerMethodField()
    recommended_products = serializers.SerializerMethodField()
    
    # Available colors and sizes for variant selection
    available_colors = serializers.SerializerMethodField()
    available_sizes = serializers.SerializerMethodField()
    available_patterns = serializers.SerializerMethodField()
    available_qualities = serializers.SerializerMethodField()
    
    # Real review data
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_percentages = serializers.SerializerMethodField()
    
    # Price fields from first variant (for display purposes)
    price = serializers.SerializerMethodField()
    old_price = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'short_description', 'long_description',
            'main_image', 'price', 'old_price', 'is_on_sale', 'discount_percentage',
            'average_rating', 'review_count', 'review_percentages', 'category', 'subcategory',
            'brand', 'material', 'dimensions', 'weight', 'warranty', 'assembly_required', 'estimated_delivery_days',
            'screen_offer', 'style_description', 'user_guide', 'care_instructions', 'what_in_box',
            'images', 'variants', 'features', 'about_items', 'offers',
            'buy_with_products', 'inspired_products', 'frequently_viewed_products',
            'similar_products', 'recommended_products',
            'available_colors', 'available_sizes', 'available_patterns', 'available_qualities',
            'meta_title', 'meta_description', 'is_featured', 'created_at', 'updated_at'
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
    
    def get_buy_with_products(self, obj):
        """Get 'Buy it with



' recommended products"""
        recommendations = ProductRecommendation.objects.filter(
            product=obj,
            recommendation_type='buy_with',
            is_active=True
        ).select_related('recommended_product')[:10]
        
        return ProductListSerializer([rec.recommended_product for rec in recommendations], many=True).data
    
    def get_inspired_products(self, obj):
        """Get 'Inspired by browsing history' products"""
        recommendations = ProductRecommendation.objects.filter(
            product=obj,
            recommendation_type='inspired_by',
            is_active=True
        ).select_related('recommended_product')[:10]
        
        return ProductListSerializer([rec.recommended_product for rec in recommendations], many=True).data
    
    def get_frequently_viewed_products(self, obj):
        """Get frequently viewed products"""
        recommendations = ProductRecommendation.objects.filter(
            product=obj,
            recommendation_type='frequently_viewed',
            is_active=True
        ).select_related('recommended_product')[:10]
        
        return ProductListSerializer([rec.recommended_product for rec in recommendations], many=True).data
    
    def get_similar_products(self, obj):
        """Get similar products"""
        recommendations = ProductRecommendation.objects.filter(
            product=obj,
            recommendation_type='similar',
            is_active=True
        ).select_related('recommended_product')[:10]
        
        return ProductListSerializer([rec.recommended_product for rec in recommendations], many=True).data
    
    def get_recommended_products(self, obj):
        """Get recommended products"""
        recommendations = ProductRecommendation.objects.filter(
            product=obj,
            recommendation_type='recommended',
            is_active=True
        ).select_related('recommended_product')[:10]
        
        return ProductListSerializer([rec.recommended_product for rec in recommendations], many=True).data
    
    def get_available_colors(self, obj):
        """Get available colors for this product"""
        colors = obj.variants.filter(is_active=True).values('color__id', 'color__name', 'color__hex_code').distinct()
        return list(colors)
    
    def get_available_sizes(self, obj):
        """Get available sizes for this product"""
        sizes = obj.variants.filter(is_active=True).values_list('size', flat=True).distinct()
        return [size for size in sizes if size]
    
    def get_available_patterns(self, obj):
        """Get available patterns for this product"""
        patterns = obj.variants.filter(is_active=True).values_list('pattern', flat=True).distinct()
        return [pattern for pattern in patterns if pattern]
    
    def get_available_qualities(self, obj):
        """Get available qualities for this product"""
        qualities = obj.variants.filter(is_active=True).values_list('quality', flat=True).distinct()
        return [quality for quality in qualities if quality]
    
    def get_review_count(self, obj):
        """Get actual review count from database"""
        return obj.reviews.filter(is_approved=True).count()
    
    def get_average_rating(self, obj):
        """Get actual average rating from database"""
        from django.db.models import Avg
        avg_rating = obj.reviews.filter(is_approved=True).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating']
        return round(float(avg_rating), 1) if avg_rating else 0.0
    
    def get_review_percentages(self, obj):
        """Get review percentage breakdown by star rating"""
        from django.db.models import Count
        from django.db.models import Case, When, IntegerField
        
        # Get review counts by rating
        rating_counts = obj.reviews.filter(is_approved=True).aggregate(
            five_star=Count('id', filter=Q(rating=5)),
            four_star=Count('id', filter=Q(rating=4)),
            three_star=Count('id', filter=Q(rating=3)),
            two_star=Count('id', filter=Q(rating=2)),
            one_star=Count('id', filter=Q(rating=1)),
            total=Count('id')
        )
        
        total_reviews = rating_counts['total']
        if total_reviews == 0:
            return {
                '5': 0, '4': 0, '3': 0, '2': 0, '1': 0
            }
        
        return {
            '5': round((rating_counts['five_star'] / total_reviews) * 100, 1),
            '4': round((rating_counts['four_star'] / total_reviews) * 100, 1),
            '3': round((rating_counts['three_star'] / total_reviews) * 100, 1),
            '2': round((rating_counts['two_star'] / total_reviews) * 100, 1),
            '1': round((rating_counts['one_star'] / total_reviews) * 100, 1),
        }


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    # Attachments removed from public API - only visible in admin panel
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'user_name', 'user_username', 'rating', 'title', 'comment',
            'is_verified_purchase', 'created_at'
        ]
        read_only_fields = ['user', 'product']


class ProductSearchSerializer(serializers.ModelSerializer):
    """Lightweight serializer for search results"""
    category = serializers.CharField(source='category.name', read_only=True)
    subcategory = serializers.CharField(source='subcategory.name', read_only=True)
    
    # Price fields from first variant (for display purposes)
    price = serializers.SerializerMethodField()
    old_price = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'short_description', 'main_image',
            'price', 'old_price', 'is_on_sale', 'discount_percentage',
            'average_rating', 'review_count', 'category', 'subcategory', 'brand'
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


class ProductFilterSerializer(serializers.Serializer):
    """Serializer for product filtering parameters"""
    # Category filters
    category = serializers.CharField(required=False)
    subcategory = serializers.CharField(required=False)
    
    # Price filters
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    # Color filter
    color = serializers.CharField(required=False)
    
    # Material filter
    material = serializers.CharField(required=False)
    
    # Rating filter
    min_rating = serializers.DecimalField(max_digits=3, decimal_places=2, required=False)
    
    # Brand filter (though we only have Sixpine)
    brand = serializers.CharField(required=False)
    
    # Search query
    q = serializers.CharField(required=False)
    
    # Sorting
    sort = serializers.ChoiceField(choices=[
        ('relevance', 'Relevance'),
        ('price_low_to_high', 'Price: Low to High'),
        ('price_high_to_low', 'Price: High to Low'),
        ('newest', 'Newest First'),
        ('rating', 'Customer Rating'),
        ('popularity', 'Most Popular'),
    ], required=False, default='relevance')
    
    # Pagination
    page = serializers.IntegerField(required=False, default=1)
    page_size = serializers.IntegerField(required=False, default=20)


class BrowsingHistorySerializer(serializers.ModelSerializer):
    """Serializer for browsing history"""
    product = ProductListSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    subcategory = SubcategorySerializer(read_only=True)
    
    class Meta:
        model = BrowsingHistory
        fields = [
            'id', 'product', 'category', 'subcategory', 
            'viewed_at', 'view_count', 'last_viewed'
        ]
        read_only_fields = ['user', 'viewed_at', 'last_viewed']


class WishlistSerializer(serializers.ModelSerializer):
    """Serializer for wishlist items"""
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'added_at', 'updated_at']
        read_only_fields = ['user', 'added_at', 'updated_at']


class WishlistCreateSerializer(serializers.Serializer):
    """Serializer for creating wishlist items"""
    product_id = serializers.IntegerField(required=True)
    
    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive")
        return value