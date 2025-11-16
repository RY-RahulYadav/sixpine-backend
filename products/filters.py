import django_filters
from django.db.models import Q, Avg, Count, Min, Max, F
from .models import Product, Category, Subcategory, Color, Material, Discount, ProductVariant


class ProductFilter(django_filters.FilterSet):
    """Advanced product filtering"""
    
    # Category filters
    category = django_filters.CharFilter(field_name='category__slug', lookup_expr='iexact')
    subcategory = django_filters.CharFilter(field_name='subcategory__slug', lookup_expr='iexact')
    
    # Price range filters - now filter by variant prices
    min_price = django_filters.NumberFilter(field_name='variants__price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='variants__price', lookup_expr='lte')
    
    # Color filter
    color = django_filters.CharFilter(method='filter_by_color')
    
    # Material filter
    material = django_filters.CharFilter(field_name='material__name', lookup_expr='icontains')
    
    # Rating filter
    min_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    
    # Brand filter
    brand = django_filters.CharFilter(field_name='brand', lookup_expr='icontains')
    
    # Vendor filter - handle special case for Sixpine (vendor=0 means vendor=None)
    vendor = django_filters.NumberFilter(method='filter_by_vendor')
    
    # Search query
    q = django_filters.CharFilter(method='filter_search')
    
    # Special filters
    is_featured = django_filters.BooleanFilter(field_name='is_featured')
    # is_on_sale removed - now calculated from variant old_price vs price
    # Discount filter - filter products having variants with at least this discount percentage
    min_discount = django_filters.NumberFilter(method='filter_by_discount')
    
    class Meta:
        model = Product
        fields = ['category', 'subcategory', 'min_price', 'max_price', 'color', 'material', 'min_rating', 'brand', 'vendor', 'q', 'min_discount']
    
    def filter_by_vendor(self, queryset, name, value):
        """Filter products by vendor - handle Sixpine (vendor=0) specially"""
        if value is not None:
            if value == 0:
                # Sixpine products have vendor=None
                return queryset.filter(vendor__isnull=True)
            else:
                return queryset.filter(vendor_id=value)
        return queryset
    
    def filter_by_color(self, queryset, name, value):
        """Filter products by color through variants"""
        if value:
            return queryset.filter(variants__color__name__icontains=value, variants__is_active=True).distinct()
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search across multiple fields"""
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(short_description__icontains=value) |
                Q(long_description__icontains=value) |
                Q(category__name__icontains=value) |
                Q(subcategory__name__icontains=value) |
                Q(brand__icontains=value) |
                Q(material__icontains=value)
            ).distinct()
        return queryset
    
    def filter_by_discount(self, queryset, name, value):
        """Filter products by discount percentage (calculated from variant prices)"""
        if value:
            # Filter products that have variants with discount >= value
            # Discount = ((old_price - price) / old_price) * 100
            return queryset.filter(
                variants__old_price__isnull=False,
                variants__price__isnull=False,
                variants__is_active=True
            ).annotate(
                discount_percent=((F('variants__old_price') - F('variants__price')) / F('variants__old_price')) * 100
            ).filter(discount_percent__gte=value).distinct()
        return queryset


class ProductSortFilter:
    """Product sorting options"""
    
    SORT_OPTIONS = {
        'relevance': '-created_at',  # Default to newest for relevance
        'price_low_to_high': 'min_variant_price',
        'price_high_to_low': '-min_variant_price',
        'newest': '-created_at',
        'rating': '-average_rating',
        'popularity': '-review_count',
    }
    
    @classmethod
    def apply_sorting(cls, queryset, sort_option):
        """Apply sorting to queryset"""
        if sort_option in ['price_low_to_high', 'price_high_to_low']:
            # Annotate with minimum variant price for sorting
            queryset = queryset.annotate(
                min_variant_price=Min('variants__price', filter=Q(variants__is_active=True))
            )
            if sort_option == 'price_low_to_high':
                return queryset.order_by('min_variant_price', '-created_at')
            else:
                return queryset.order_by('-min_variant_price', '-created_at')
        elif sort_option in cls.SORT_OPTIONS:
            return queryset.order_by(cls.SORT_OPTIONS[sort_option])
        return queryset.order_by('-created_at')  # Default sorting


class ProductAggregationFilter:
    """Get filter options for frontend"""
    
    @classmethod
    def get_filter_options(cls, queryset):
        """Get available filter options - all categories/subcategories, but filtered colors/materials/brands"""
        # Get ALL active categories (not filtered by products)
        categories = Category.objects.filter(
            is_active=True
        ).values('id', 'name', 'slug').order_by('name')
        
        # Get ALL active subcategories (not filtered by products)
        subcategories = Subcategory.objects.filter(
            is_active=True
        ).values('id', 'name', 'slug', 'category_id').order_by('category__name', 'name')
        
        # Get available colors (only from products that exist)
        colors = Color.objects.filter(
            # variants__product__in=queryset,
            # variants__is_active=True,
            is_active=True
        ).distinct().values('id', 'name', 'hex_code').order_by('name')
        
        # Get available materials (only from products that exist)
        materials = Material.objects.filter(
            # products__in=queryset,
            is_active=True
        ).distinct().values('id', 'name', 'description')
        
        # Get price range from variants (only from products that exist)
        # Get price range from active variants of products in queryset
        variant_prices = ProductVariant.objects.filter(
            product__in=queryset,
            is_active=True
        ).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        price_range = variant_prices
        
        # Get available brands (only from products that exist)
        brands = queryset.values_list('brand', flat=True).distinct()
        # Get discount options (from Discount model)
        discounts = Discount.objects.filter(is_active=True).values('percentage', 'label').order_by('percentage')
        
        return {
            'categories': list(categories),
            'subcategories': list(subcategories),
            'colors': list(colors),
            'materials': list(materials),
            'brands': list(brands),
            'price_range': price_range,
            'discounts': list(discounts),
        }
