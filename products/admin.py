from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Category, Subcategory, Color, Material, Product, ProductImage, ProductVariant,
    ProductReview, ProductRecommendation, ProductSpecification,
    ProductFeature, ProductOffer 
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'sort_order', 'product_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order', 'name']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug', 'is_active', 'sort_order', 'product_count', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'category__name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['category', 'sort_order', 'name']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'hex_code', 'color_preview', 'is_active', 'variant_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    ordering = ['name']
    
    def color_preview(self, obj):
        if obj.hex_code:
            return format_html(
                '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
                obj.hex_code
            )
        return '-'
    color_preview.short_description = 'Color'
    
    def variant_count(self, obj):
        return obj.variants.count()
    variant_count.short_description = 'Variants'


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'product_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'sort_order', 'is_active']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['color', 'size', 'pattern', 'price', 'old_price', 'stock_quantity', 'is_in_stock', 'is_active']


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1
    fields = ['name', 'value', 'sort_order', 'is_active']


class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1
    fields = ['feature', 'sort_order', 'is_active']


class ProductOfferInline(admin.TabularInline):
    model = ProductOffer
    extra = 1
    fields = ['title', 'description', 'discount_percentage', 'discount_amount', 'valid_from', 'valid_until', 'is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'subcategory', 'price', 'old_price', 'discount_percentage',
        'average_rating', 'review_count', 'is_featured', 'is_active', 'created_at'
    ]
    list_filter = [
        'category', 'subcategory', 'is_featured', 'is_active', 'is_on_sale',
        'assembly_required', 'created_at'
    ]
    search_fields = ['title', 'short_description', 'brand', 'material']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['discount_percentage', 'average_rating', 'review_count', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'short_description', 'long_description')
        }),
        ('Categorization', {
            'fields': ('category', 'subcategory', 'brand')
        }),
        ('Pricing', {
            'fields': ('price', 'old_price', 'is_on_sale', 'discount_percentage')
        }),
        ('Product Details', {
            'fields': ('main_image', 'material', 'dimensions', 'weight', 'warranty', 'assembly_required')
        }),
        ('SEO & Display', {
            'fields': ('meta_title', 'meta_description', 'is_featured', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [
        ProductImageInline,
        ProductVariantInline,
        ProductSpecificationInline,
        ProductFeatureInline,
        ProductOfferInline,
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'subcategory')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'alt_text', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['product__title', 'alt_text']
    ordering = ['product', 'sort_order']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />',
                obj.image
            )
        return '-'
    image_preview.short_description = 'Preview'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'color', 'size', 'pattern', 'price', 'stock_quantity',
        'is_in_stock', 'is_active', 'created_at'
    ]
    list_filter = ['color', 'is_in_stock', 'is_active', 'created_at']
    search_fields = ['product__title', 'color__name', 'size', 'pattern']
    ordering = ['product', 'color', 'size', 'pattern']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'user', 'rating', 'title', 'is_verified_purchase',
        'is_approved', 'created_at'
    ]
    list_filter = ['rating', 'is_verified_purchase', 'is_approved', 'created_at']
    search_fields = ['product__title', 'user__username', 'user__email', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(ProductRecommendation)
class ProductRecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'recommended_product', 'recommendation_type',
        'sort_order', 'is_active', 'created_at'
    ]
    list_filter = ['recommendation_type', 'is_active', 'created_at']
    search_fields = ['product__title', 'recommended_product__title']
    ordering = ['product', 'sort_order']


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'value', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['product__title', 'name', 'value']
    ordering = ['product', 'sort_order']


@admin.register(ProductFeature)
class ProductFeatureAdmin(admin.ModelAdmin):
    list_display = ['product', 'feature_preview', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['product__title', 'feature']
    ordering = ['product', 'sort_order']
    
    def feature_preview(self, obj):
        return obj.feature[:50] + '...' if len(obj.feature) > 50 else obj.feature
    feature_preview.short_description = 'Feature'


@admin.register(ProductOffer)
class ProductOfferAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'title', 'discount_percentage', 'discount_amount',
        'is_active', 'valid_from', 'valid_until', 'created_at'
    ]
    list_filter = ['is_active', 'valid_from', 'valid_until', 'created_at']
    search_fields = ['product__title', 'title', 'description']
    ordering = ['-created_at']