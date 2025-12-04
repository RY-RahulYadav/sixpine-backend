from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class Category(models.Model):
    """Main product categories like Sofas, Recliners, etc."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    # store an external or CDN URL to the category image instead of uploading files
    image = models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['sort_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    """Subcategories like 3-Seater, 2-Seater for Sofas"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Subcategories"
        unique_together = ['name', 'category']
        ordering = ['sort_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Color(models.Model):
    """Product colors for filtering"""
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, blank=True)  # For color display
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Material(models.Model):
    """Product materials for filtering"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Main product model"""
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True, help_text='Stock Keeping Unit - unique product identifier')
    short_description = models.TextField(max_length=500)
    long_description = models.TextField(blank=True)
    
    # Categorization
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='products', null=True, blank=True)  # Keep for backward compatibility
    subcategories = models.ManyToManyField(Subcategory, related_name='product_set', blank=True, help_text='Multiple subcategories this product belongs to (e.g., 1 Seater, 2 Seater, 3 Seater)')
    
    # Note: Pricing is now only in ProductVariant model, not in Product
    
    # Images
    # store an external or CDN URL to the product's main image
    main_image = models.URLField(max_length=500, blank=True, null=True)
    
    # Ratings and Reviews
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    review_count = models.PositiveIntegerField(default=0)
    
    # Product Details - Multi-vendor support
    vendor = models.ForeignKey('accounts.Vendor', on_delete=models.CASCADE, related_name='products', null=True, blank=True, help_text='Vendor/Seller who owns this product')
    brand = models.CharField(max_length=100, blank=True, help_text='Brand name (can be different from vendor brand)')
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    dimensions = models.CharField(max_length=100, blank=True)  # e.g., "L x W x H"
    weight = models.CharField(max_length=50, blank=True)
    warranty = models.CharField(max_length=100, blank=True)
    assembly_required = models.BooleanField(default=False)
    estimated_delivery_days = models.PositiveIntegerField(default=4, help_text='Estimated delivery time in days (e.g., 4 for 4 days)')
    
    # Additional Product Information
    screen_offer = models.JSONField(default=list, blank=True, help_text="Array of screen offer objects with 'title' and 'description' fields, or strings for backward compatibility")
    style_description = models.TextField(blank=True, null=True, help_text="Detailed style description for the Style section")
    user_guide = models.TextField(blank=True, null=True, help_text="User guide instructions")
    care_instructions = models.TextField(blank=True, null=True, help_text="Care and maintenance instructions")
    what_in_box = models.TextField(blank=True, null=True, help_text="What is included in the box")
    
    # SEO and Display
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    """Additional product images"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    # store an external or CDN URL to the gallery image
    image = models.URLField(max_length=500, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f"{self.product.title} - Image {self.sort_order}"


class ProductVariantImage(models.Model):
    """Additional images for product variants"""
    variant = models.ForeignKey('ProductVariant', on_delete=models.CASCADE, related_name='images')
    # store an external or CDN URL to the variant gallery image
    image = models.URLField(max_length=500, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return f"{self.variant.product.title} - {self.variant.title} - Image {self.sort_order}"


class ProductVariant(models.Model):
    """Product variants for different colors, sizes, etc."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=50, blank=True)  # e.g., "S", "M", "L" or "3-Seater", "2-Seater"
    pattern = models.CharField(max_length=100, blank=True)  # e.g., "Classic", "Modern"
    quality = models.CharField(max_length=100, blank=True)  # e.g., "Premium", "Standard", "Luxury"
    subcategories = models.ManyToManyField(Subcategory, related_name='variants', blank=True, help_text='Subcategories this variant belongs to (e.g., 1 Seater, 2 Seater)')
    
    # Variant title for display (e.g., "White 4-Door Modern")
    title = models.CharField(max_length=200, blank=True)
    
    # Variant-specific pricing (required - variants are the actual products)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text='Price is required for variants')
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    discount_percentage = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)], help_text='Discount percentage calculated from old_price and price')
    
    # Stock management
    stock_quantity = models.PositiveIntegerField(default=0)
    is_in_stock = models.BooleanField(default=True)
    
    # Variant-specific image
    # store an external or CDN URL to the variant image
    image = models.URLField(max_length=500, blank=True, null=True)
    
    # Variant-specific information (like specifications but for Measurement, Style, Features, User Guide)
    # Measurement specifications as key-value pairs (JSONField)
    measurement_specs = models.JSONField(default=dict, blank=True, help_text="Key-value pairs for measurement details (e.g., {'Dimensions': '64 x 29 x 36 inch', 'Weight': '45 kg'})")
    
    # Style specifications as key-value pairs (JSONField)
    style_specs = models.JSONField(default=dict, blank=True, help_text="Key-value pairs for style details (e.g., {'Colour': 'Grey & Beige', 'Style': 'Modern', 'Shape': 'Rectangular'})")
    
    # Features as key-value pairs (JSONField)
    features = models.JSONField(default=dict, blank=True, help_text="Key-value pairs for features (e.g., {'Weight Capacity Maximum': '450 Kilograms', 'Seating Capacity': '3.0'})")
    
    # User guide as key-value pairs (JSONField)
    user_guide = models.JSONField(default=dict, blank=True, help_text="Key-value pairs for user guide (e.g., {'Assembly': 'Required', 'Care Instructions': 'Wipe with dry cloth'})")
    
    # Display
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'color', 'size', 'pattern', 'quality']
        ordering = ['color__name', 'size', 'pattern', 'quality']

    def save(self, *args, **kwargs):
        # Generate title if not set
        if not self.title:
            variant_parts = []
            if self.color:
                variant_parts.append(self.color.name)
            if self.size:
                variant_parts.append(self.size)
            if self.pattern:
                variant_parts.append(self.pattern)
            if self.quality:
                variant_parts.append(self.quality)
            self.title = ' '.join(variant_parts) if variant_parts else ''
        
        # Price is required - variants are the actual products
        if not self.price:
            raise ValueError("Price is required for ProductVariant. Variants are the actual products.")
        
        # Calculate discount percentage
        if self.old_price and self.old_price > self.price:
            self.discount_percentage = int(((self.old_price - self.price) / self.old_price) * 100)
        else:
            self.discount_percentage = 0
            
        # Update stock status
        self.is_in_stock = self.stock_quantity > 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.title} - {self.title}" if self.title else f"{self.product.title} - Variant {self.id}"


class ProductReview(models.Model):
    """Product reviews and ratings"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False, help_text='Review must be approved by admin or vendor before appearing on product page')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.title} - {self.rating} stars"


class ProductRecommendation(models.Model):
    """Product recommendations for 'Buy it with' and 'Inspired by' sections"""
    RECOMMENDATION_TYPES = [
        ('buy_with', 'Buy it with'),
        ('inspired_by', 'Inspired by browsing history'),
        ('frequently_viewed', 'Frequently viewed'),
        ('similar', 'Similar products'),
        ('recommended', 'Recommended for you'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommendations')
    recommended_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommended_by')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'recommended_product', 'recommendation_type']
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return f"{self.product.title} -> {self.recommended_product.title} ({self.recommendation_type})"


class ProductSpecification(models.Model):
    """Product specifications and key details - linked to variants"""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='specifications')
    name = models.CharField(max_length=100)  # e.g., "Brand", "Depth", "Style"
    value = models.CharField(max_length=200)  # e.g., "Atomberg", "12 inch", "Modern"
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.variant.product.title} - {self.variant.title} - {self.name}: {self.value}"


class ProductFeature(models.Model):
    """Product features for Features box"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='features')
    feature = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']


    def __str__(self):
        return f"{self.product.title} - {self.feature[:50]}..."


class ProductAboutItem(models.Model):
    """Product 'About This Item' bullet points - separate from features"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='about_items')
    item = models.TextField(help_text="Bullet point for 'About This Item' section")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']
        verbose_name = "About This Item"
        verbose_name_plural = "About This Item"

    def __str__(self):
        return f"{self.product.title} - {self.item[:50]}..."


class ProductOffer(models.Model):
    """Product offers and promotions"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='offers')
    title = models.CharField(max_length=200)
    description = models.TextField()
    discount_percentage = models.PositiveIntegerField(null=True, blank=True, validators=[MaxValueValidator(100)])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.title} - {self.title}"


class Discount(models.Model):
    """Predefined discount filter options for product pages (e.g., 10%, 20%, 30%, 50%)
    
    Note: This is NOT for payment discounts at checkout. 
    For checkout discounts, use the Coupon model instead.
    This model is used for filtering products by discount percentage on product listing pages.
    """
    percentage = models.PositiveIntegerField(unique=True, validators=[MaxValueValidator(100)])
    label = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['percentage']
        verbose_name = "Discount Filter Option"
        verbose_name_plural = "Discount Filter Options"

    def save(self, *args, **kwargs):
        if not self.label:
            self.label = f"{self.percentage}%"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.percentage}%"


class Coupon(models.Model):
    """Coupon codes for discounts"""
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    COUPON_TYPES = [
        ('sixpine', 'Sixpine Products Only - Reduces product prices'),
        ('common', 'All Products (Common) - Reduces product prices'),
        ('seller', 'Platform Fee & Tax Only - Does NOT reduce seller product prices'),
    ]
    
    code = models.CharField(max_length=50, db_index=True)
    coupon_type = models.CharField(
        max_length=20, 
        choices=COUPON_TYPES, 
        default='common',
        help_text='Type of coupon: Sixpine products only, all products, or seller products (reduces only platform fee and tax)'
    )
    vendor = models.ForeignKey('accounts.Vendor', on_delete=models.CASCADE, related_name='coupons', null=True, blank=True, help_text='Vendor who owns this coupon. If null, coupon applies to all products.')
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of times this coupon can be used")
    used_count = models.PositiveIntegerField(default=0)
    one_time_use_per_user = models.BooleanField(default=False, help_text="If True, each user can use this coupon only once")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['code', 'vendor']]  # Code must be unique per vendor
        ordering = ['-created_at']
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
    
    def __str__(self):
        coupon_type_label = dict(self.COUPON_TYPES).get(self.coupon_type, self.coupon_type)
        if self.vendor:
            return f"{self.code} - {self.vendor.brand_name} ({coupon_type_label})"
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else '₹'} ({coupon_type_label})"
    
    def is_valid(self):
        """Check if coupon is currently valid"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.usage_limit is None or self.used_count < self.usage_limit)
        )
    
    def can_be_used_by_user(self, user):
        """Check if coupon can be used by a specific user"""
        if not self.is_valid():
            return False, "Coupon is not valid"
        
        if self.one_time_use_per_user:
            from orders.models import Order
            # Check if user has already used this coupon
            if Order.objects.filter(user=user, coupon=self).exists():
                return False, "This coupon can only be used once per user"
        
        return True, "Valid"
    
    def calculate_discount(self, order_amount, vendor_products_amount=None, platform_fee=None, tax_amount=None):
        """Calculate discount amount for given order amount
        
        For seller coupons (coupon_type='seller'), discount is calculated only on 
        platform fee and tax, not on product prices.
        
        Args:
            order_amount: Total order amount
            vendor_products_amount: Amount for vendor-specific products (if applicable)
            platform_fee: Platform fee amount (required for seller coupons)
            tax_amount: Tax amount (required for seller coupons)
        """
        from decimal import Decimal
        
        # Convert order_amount to Decimal to ensure proper calculation
        if not isinstance(order_amount, Decimal):
            order_amount = Decimal(str(order_amount))
        
        # Seller coupons: discount ONLY on platform fee and tax (NOT on seller product prices)
        if self.coupon_type == 'seller':
            if platform_fee is None or tax_amount is None:
                return Decimal('0'), "Platform fee and tax amounts are required for seller coupons"
            
            if not isinstance(platform_fee, Decimal):
                platform_fee = Decimal(str(platform_fee))
            if not isinstance(tax_amount, Decimal):
                tax_amount = Decimal(str(tax_amount))
            
            # Check minimum order amount on total order
            if order_amount < self.min_order_amount:
                return Decimal('0'), f"Minimum order amount of ₹{self.min_order_amount} required"
            
            # Calculate discount on platform fee + tax ONLY (NOT on seller product prices)
            applicable_amount = platform_fee + tax_amount
            
            if applicable_amount <= 0:
                return Decimal('0'), "No platform fee or tax to discount"
            
            if self.discount_type == 'percentage':
                discount = (applicable_amount * self.discount_value) / Decimal('100')
                if self.max_discount_amount:
                    discount = min(discount, self.max_discount_amount)
            else:
                discount = min(self.discount_value, applicable_amount)
            
            return discount, "Discount applied on platform fee and tax only (seller product prices unchanged)"
        
        # Sixpine and common coupons: discount on product prices
        # If coupon is vendor-specific, use vendor_products_amount if provided
        if self.vendor and vendor_products_amount is not None:
            if not isinstance(vendor_products_amount, Decimal):
                vendor_products_amount = Decimal(str(vendor_products_amount))
            # Check minimum order amount on vendor products
            if vendor_products_amount < self.min_order_amount:
                return Decimal('0'), f"Minimum order amount of ₹{self.min_order_amount} required for vendor products"
            # Calculate discount on vendor products only
            applicable_amount = vendor_products_amount
        else:
            # Check minimum order amount
            if order_amount < self.min_order_amount:
                return Decimal('0'), f"Minimum order amount of ₹{self.min_order_amount} required"
            applicable_amount = order_amount
        
        if self.discount_type == 'percentage':
            # Both are now Decimal, so calculation is safe
            discount = (applicable_amount * self.discount_value) / Decimal('100')
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:
            discount = min(self.discount_value, applicable_amount)
        
        return discount, "Discount applied"


class BrowsingHistory(models.Model):
    """Track user browsing history for products and categories"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='browsing_history')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='browsing_history')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='browsing_history', null=True, blank=True)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='browsing_history', null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    view_count = models.PositiveIntegerField(default=1)
    last_viewed = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Browsing History'
        verbose_name_plural = 'Browsing History'
        db_table = 'browsing_history'
        ordering = ['-last_viewed']
        unique_together = ['user', 'product']
        indexes = [
            models.Index(fields=['user', '-last_viewed'], name='browsing_hi_user_id_941c7b_idx'),
            models.Index(fields=['user', 'category'], name='browsing_hi_user_id_3df6af_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.view_count} views)"


class Wishlist(models.Model):
    """User wishlist for products"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items')
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        db_table = 'wishlist'
        ordering = ['-added_at']
        unique_together = ['user', 'product']
        indexes = [
            models.Index(fields=['user', '-added_at'], name='wishlist_user_added_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.title}"