import django_filters
from django.db.models import Q, Avg, Count, Min, Max, F
from .models import Product, Category, Subcategory, Color, Material, Discount, ProductVariant


class ProductFilter(django_filters.FilterSet):
    """Advanced product filtering"""
    
    # Category filters
    category = django_filters.CharFilter(field_name='category__slug', lookup_expr='iexact')
    subcategory = django_filters.CharFilter(method='filter_by_subcategory')
    
    # Price range filters - filter products that have at least one variant in the price range
    min_price = django_filters.NumberFilter(method='filter_by_min_price')
    max_price = django_filters.NumberFilter(method='filter_by_max_price')
    
    # Color filter
    color = django_filters.CharFilter(method='filter_by_color')
    
    # Material filter
    material = django_filters.CharFilter(method='filter_by_material')
    
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
    
    def filter_by_min_price(self, queryset, name, value):
        """Filter products that have at least one variant with price >= min_price"""
        if value is not None:
            return queryset.filter(
                variants__price__gte=value,
                variants__is_active=True
            ).distinct()
        return queryset
    
    def filter_by_max_price(self, queryset, name, value):
        """Filter products that have at least one variant with price <= max_price"""
        if value is not None:
            return queryset.filter(
                variants__price__lte=value,
                variants__is_active=True
            ).distinct()
        return queryset
    
    def filter_by_color(self, queryset, name, value):
        """Filter products by color through variants - supports comma-separated colors"""
        if value:
            # Handle comma-separated color names
            color_names = [c.strip() for c in value.split(',') if c.strip()]
            if color_names:
                # Use Q objects to match any of the colors
                from django.db.models import Q
                color_query = Q()
                for color_name in color_names:
                    color_query |= Q(variants__color__name__iexact=color_name, variants__is_active=True)
                return queryset.filter(color_query).distinct()
        return queryset
    
    def filter_by_material(self, queryset, name, value):
        """Filter products by material - supports comma-separated materials"""
        if value:
            # Handle comma-separated material names
            material_names = [m.strip() for m in value.split(',') if m.strip()]
            if material_names:
                # Use Q objects to match any of the materials
                from django.db.models import Q
                material_query = Q()
                for material_name in material_names:
                    material_query |= Q(material__name__iexact=material_name)
                return queryset.filter(material_query).distinct()
        return queryset
    
    def filter_by_subcategory(self, queryset, name, value):
        """Filter products by subcategory - filter products that have variants with this subcategory"""
        if value:
            # First try to find subcategory by slug
            from .models import Subcategory
            try:
                subcategory = Subcategory.objects.get(slug=value, is_active=True)
                subcategory_id = subcategory.id
            except Subcategory.DoesNotExist:
                # If not found by slug, try to find by name
                try:
                    subcategory = Subcategory.objects.filter(name__iexact=value.replace('-', ' '), is_active=True).first()
                    if subcategory:
                        subcategory_id = subcategory.id
                    else:
                        # If still not found, return empty queryset
                        return queryset.none()
                except:
                    return queryset.none()
            
            # Filter products that have variants with this subcategory in their subcategories ManyToMany
            # This ensures we only get products that have at least one variant with the selected subcategory
            return queryset.filter(
                variants__subcategories__id=subcategory_id,
                variants__is_active=True
            ).distinct()
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search across multiple fields with regex matching for title and variant titles"""
        if value:
            # Use regex for title field (case-insensitive), icontains for other fields
            # Also search in variant titles since we're expanding variants
            # This allows flexible pattern matching on product titles and variant titles
            return queryset.filter(
                Q(title__iregex=value) |
                Q(variants__title__iregex=value, variants__is_active=True) |
                Q(short_description__icontains=value) |
                Q(long_description__icontains=value) |
                Q(category__name__icontains=value) |
                Q(subcategory__name__icontains=value) |
                Q(brand__icontains=value) |
                Q(material__name__icontains=value)
            ).distinct()
        return queryset
    
    def filter_by_discount(self, queryset, name, value):
        """Filter products that have at least one variant with discount >= value
        
        This is a BROAD filter at product level - keeps products that potentially have
        qualifying variants. The precise variant-level filtering happens during variant
        expansion in the view to show only variants meeting the threshold.
        
        We check:
        1. Variants with stored discount_percentage >= value
        2. Variants with old_price > price (indicating potential discount)
        
        The view then does exact calculations to show only qualifying variants.
        """
        if value:
            from django.db.models import Q
            
            # Keep products that have variants with stored discount_percentage >= threshold
            # OR variants that have old_price/price set (might have sufficient discount)
            return queryset.filter(
                Q(
                    variants__discount_percentage__gte=value,
                    variants__is_active=True
                ) |
                Q(
                    variants__old_price__isnull=False,
                    variants__price__isnull=False,
                    variants__old_price__gt=F('variants__price'),
                    variants__is_active=True
                )
            ).distinct()
        return queryset


class ProductSortFilter:
    """Product sorting options"""
    
    SORT_OPTIONS = {
        'relevance': '-created_at',  # Default to newest for relevance
        'price_low_to_high': 'min_variant_price',
        'price_high_to_low': '-min_variant_price',
        'newest': '-created_at',
        'date_new_to_old': '-created_at',  # New to Old
        'date_old_to_new': 'created_at',   # Old to New
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
