from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count, Prefetch, Min, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import (
    Product, Category, Subcategory, Color, Material, ProductVariant, ProductVariantImage,
    ProductReview, ProductRecommendation, ProductSpecification,
    ProductFeature, ProductOffer, BrowsingHistory, Discount
)
from accounts.models import Vendor
from .serializers import (
    ProductListSerializer, ProductDetailSerializer, ProductSearchSerializer,
    CategorySerializer, SubcategorySerializer, ColorSerializer, MaterialSerializer,
    ProductReviewSerializer, ProductFilterSerializer, ProductOfferSerializer,
    BrowsingHistorySerializer
)
from .filters import ProductFilter, ProductSortFilter, ProductAggregationFilter


class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination for product lists"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProductListView(generics.ListAPIView):
    """Product listing with advanced filtering and sorting"""
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'short_description', 'category__name', 'subcategory__name', 'brand', 'material']
    ordering_fields = ['price', 'created_at', 'average_rating', 'review_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get products with optimized queries"""
        queryset = Product.objects.filter(is_active=True).select_related(
            'category', 'subcategory'
        ).prefetch_related(
            'images',
            'reviews',
            Prefetch('variants', queryset=ProductVariant.objects.filter(is_active=True).select_related('color').prefetch_related('images'))
        )
        
        # Apply sorting
        sort_option = self.request.query_params.get('sort', 'relevance')
        queryset = ProductSortFilter.apply_sorting(queryset, sort_option)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Override list to include filter options and expand variants"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Check if we should prioritize products from user's interest categories
        # Only if user is authenticated, has interests (category names), and no category filter/search is applied
        user_interest_category_ids = []
        if request.user.is_authenticated:
            user_interests = request.user.interests or []
            if isinstance(user_interests, str):
                import json
                try:
                    user_interests = json.loads(user_interests)
                except:
                    user_interests = []
            
            # Convert category names to category IDs
            if user_interests and isinstance(user_interests, list):
                from .models import Category
                interest_categories = Category.objects.filter(
                    name__in=user_interests,
                    is_active=True
                ).values_list('id', flat=True)
                user_interest_category_ids = list(interest_categories)
        
        # Check if category filter or search query is applied
        category_filter = request.query_params.get('category') or request.query_params.get('category__slug')
        search_query = request.query_params.get('q') or request.query_params.get('search')
        
        # Prioritize products from interest categories if applicable
        if user_interest_category_ids and not category_filter and not search_query:
            from django.db.models import Case, When, IntegerField
            # Get the current sort option to preserve it within priority groups
            sort_option = request.query_params.get('sort', 'relevance')
            sort_field = ProductSortFilter.SORT_OPTIONS.get(sort_option, '-created_at')
            
            # Create a case statement to prioritize products from interest categories
            when_conditions = [When(category_id=cat_id, then=0) for cat_id in user_interest_category_ids]
            if when_conditions:
                queryset = queryset.annotate(
                    priority=Case(
                        *when_conditions,
                        default=1,
                        output_field=IntegerField()
                    )
                ).order_by('priority', sort_field)
        
        # Check if we should expand variants into separate items
        expand_variants = request.query_params.get('expand_variants', 'false').lower() == 'true'
        
        # Get filter options for the current queryset
        filter_options = ProductAggregationFilter.get_filter_options(queryset)
        
        # If expand_variants, we need to handle pagination differently
        if expand_variants:
            # Expand variants: create a list where each variant is a separate item
            expanded_results = []
            for product in queryset:
                variants = product.variants.filter(is_active=True).prefetch_related('images').all()
                if variants.exists():
                    # If product has variants, add each variant as a separate item
                    for variant in variants:
                        # Get variant images
                        variant_images = [
                            {
                                'id': img.id,
                                'image': img.image,
                                'alt_text': img.alt_text,
                                'sort_order': img.sort_order
                            }
                            for img in variant.images.filter(is_active=True).order_by('sort_order')
                        ] if hasattr(variant, 'images') else []
                        
                        expanded_results.append({
                            'id': f"{product.id}-{variant.id}",  # Unique ID for variant
                            'product_id': product.id,
                            'variant_id': variant.id,
                            'title': f"{product.title} - {variant.title}",  # Include variant title in product title
                            'slug': product.slug,
                            'product_title': product.title,  # Original product title
                            'short_description': product.short_description,
                            'main_image': variant.image if variant.image else product.main_image,
                            'images': variant_images if variant_images else [{'image': variant.image if variant.image else product.main_image}] if variant.image or product.main_image else [],
                            'price': float(variant.price) if variant.price else float(product.price),
                            'old_price': float(variant.old_price) if variant.old_price else (float(product.old_price) if product.old_price else None),
                            'is_on_sale': product.is_on_sale,
                            'discount_percentage': product.discount_percentage,
                            'average_rating': self._get_average_rating(product),
                            'review_count': product.reviews.filter(is_approved=True).count(),
                            'category': {
                                'id': product.category.id,
                                'name': product.category.name,
                                'slug': product.category.slug
                            },
                            'subcategory': {
                                'id': product.subcategory.id,
                                'name': product.subcategory.name,
                                'slug': product.subcategory.slug
                            } if product.subcategory else None,
                            'brand': product.brand,
                            'material': {
                                'id': product.material.id,
                                'name': product.material.name
                            } if product.material else None,
                            'variant': {
                                'id': variant.id,
                                'title': variant.title,
                                'color': {
                                    'id': variant.color.id,
                                    'name': variant.color.name,
                                    'hex_code': variant.color.hex_code
                                },
                                'size': variant.size,
                                'pattern': variant.pattern,
                                'price': float(variant.price) if variant.price else float(product.price),
                                'old_price': float(variant.old_price) if variant.old_price else (float(product.old_price) if product.old_price else None),
                                'stock_quantity': variant.stock_quantity,
                                'is_in_stock': variant.is_in_stock,
                                'image': variant.image if variant.image else product.main_image,
                                'images': variant_images
                            },
                            'variant_title': variant.title,  # For easy access in frontend
                            'is_featured': product.is_featured,
                            'created_at': product.created_at.isoformat()
                        })
                else:
                    # If no variants, add product as is
                    serializer = self.get_serializer(product)
                    expanded_results.append(serializer.data)
            
            # Apply sorting to expanded results
            sort_option = request.query_params.get('sort', 'relevance')
            expanded_results = self._sort_expanded_results(expanded_results, sort_option)
            
            # Manual pagination for expanded results
            page_size = int(request.query_params.get('page_size', self.pagination_class.page_size))
            page_number = int(request.query_params.get('page', 1))
            start = (page_number - 1) * page_size
            end = start + page_size
            paginated_items = expanded_results[start:end]
            
            total_count = len(expanded_results)
            total_pages = (total_count + page_size - 1) // page_size
            
            return Response({
                'count': total_count,
                'next': f"?page={page_number + 1}" if end < total_count else None,
                'previous': f"?page={page_number - 1}" if page_number > 1 else None,
                'results': paginated_items,
                'filter_options': filter_options
            })
        else:
            # Normal pagination without expansion
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_response = self.get_paginated_response(serializer.data)
                paginated_response.data['filter_options'] = filter_options
                return paginated_response
            
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'results': serializer.data,
                'filter_options': filter_options
            })
    
    def _get_average_rating(self, product):
        """Helper to get average rating"""
        from django.db.models import Avg
        avg_rating = product.reviews.filter(is_approved=True).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating']
        return round(float(avg_rating), 1) if avg_rating else 0.0
    
    def _sort_expanded_results(self, results, sort_option):
        """Sort expanded variant results"""
        if sort_option == 'price_low_to_high':
            return sorted(results, key=lambda x: x['price'])
        elif sort_option == 'price_high_to_low':
            return sorted(results, key=lambda x: x['price'], reverse=True)
        elif sort_option == 'newest':
            return sorted(results, key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_option == 'rating':
            return sorted(results, key=lambda x: x.get('average_rating', 0), reverse=True)
        else:
            return results


class ProductDetailView(generics.RetrieveAPIView):
    """Detailed product view with all related data"""
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Get product with all related data"""
        return Product.objects.filter(is_active=True).select_related(
            'category', 'subcategory'
        ).prefetch_related(
            'images',
            'specifications',
            'features',
            'offers',
            'reviews',
            Prefetch('variants', queryset=ProductVariant.objects.filter(is_active=True).select_related('color').prefetch_related('images')),
            Prefetch('recommendations__recommended_product', 
                    queryset=Product.objects.filter(is_active=True))
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to track browsing history"""
        response = super().retrieve(request, *args, **kwargs)
        
        # Track browsing history if user is authenticated
        if request.user.is_authenticated and response.status_code == 200:
            product_id = response.data.get('id')
            if product_id:
                try:
                    # Get or create browsing history entry
                    browsing_history, created = BrowsingHistory.objects.get_or_create(
                        user=request.user,
                        product_id=product_id,
                        defaults={
                            'category_id': response.data.get('category', {}).get('id'),
                            'subcategory_id': response.data.get('subcategory', {}).get('id') if response.data.get('subcategory') else None,
                        }
                    )
                    
                    if not created:
                        # Update view count and last viewed
                        browsing_history.view_count += 1
                        browsing_history.last_viewed = timezone.now()
                        # Update category/subcategory if not set
                        if not browsing_history.category_id and response.data.get('category', {}).get('id'):
                            browsing_history.category_id = response.data.get('category', {}).get('id')
                        if not browsing_history.subcategory_id and response.data.get('subcategory', {}).get('id'):
                            browsing_history.subcategory_id = response.data.get('subcategory', {}).get('id')
                        browsing_history.save()
                except Exception as e:
                    # Silently fail - don't break the product detail page if tracking fails
                    pass
        
        return response


class ProductSearchView(generics.ListAPIView):
    """Advanced product search"""
    serializer_class = ProductSearchSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'short_description', 'long_description', 'category__name', 'subcategory__name', 'brand', 'material']
    
    def get_queryset(self):
        """Get products for search"""
        return Product.objects.filter(is_active=True).select_related(
            'category', 'subcategory'
        )


class CategoryListView(generics.ListAPIView):
    """List all categories with subcategories"""
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True).prefetch_related(
            'subcategories'
        ).order_by('sort_order', 'name')


class SubcategoryListView(generics.ListAPIView):
    """List subcategories for a specific category"""
    serializer_class = SubcategorySerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            return Subcategory.objects.filter(
                category__slug=category_slug,
                is_active=True
            ).order_by('sort_order', 'name')
        return Subcategory.objects.filter(is_active=True).order_by('sort_order', 'name')


class ColorListView(generics.ListAPIView):
    """List all available colors"""
    serializer_class = ColorSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Color.objects.filter(is_active=True).order_by('name')


class MaterialListView(generics.ListAPIView):
    """List all available materials"""
    serializer_class = MaterialSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Material.objects.filter(is_active=True).order_by('name')


class ProductReviewListView(generics.ListCreateAPIView):
    """List and create product reviews"""
    serializer_class = ProductReviewSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        product_slug = self.kwargs.get('slug')
        return ProductReview.objects.filter(
            product__slug=product_slug,
            is_approved=True
        ).select_related('user').order_by('-created_at')
    
    def perform_create(self, serializer):
        product_slug = self.kwargs.get('slug')
        product = get_object_or_404(Product, slug=product_slug)
        serializer.save(product=product, user=self.request.user)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_featured_products(request):
    """Get featured products for homepage"""
    products = Product.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related('category', 'subcategory').prefetch_related(
        'images', 'variants__color'
    ).order_by('-created_at')[:10]
    
    serializer = ProductListSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_new_arrivals(request):
    """Get new arrival products"""
    products = Product.objects.filter(
        is_active=True
    ).select_related('category', 'subcategory').prefetch_related(
        'images', 'variants__color'
    ).order_by('-created_at')[:20]
    
    serializer = ProductListSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_home_data(request):
    """Get all data needed for homepage"""
    # Featured products
    featured_products = Product.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related('category', 'subcategory').prefetch_related(
        'images', 'variants__color'
    ).order_by('-created_at')[:10]
    
    # New arrivals
    new_arrivals = Product.objects.filter(
        is_active=True
    ).select_related('category', 'subcategory').prefetch_related(
        'images', 'variants__color'
    ).order_by('-created_at')[:20]
    
    # Categories
    categories = Category.objects.filter(is_active=True).prefetch_related(
        'subcategories'
    ).order_by('sort_order', 'name')
    
    return Response({
        'featured_products': ProductListSerializer(featured_products, many=True).data,
        'new_arrivals': ProductListSerializer(new_arrivals, many=True).data,
        'categories': CategorySerializer(categories, many=True).data,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_homepage_content(request):
    """Get homepage content sections for public display"""
    from admin_api.models import HomePageContent
    
    section_key = request.query_params.get('section_key', None)
    
    if section_key:
        try:
            content = HomePageContent.objects.get(section_key=section_key, is_active=True)
            return Response({
                'section_key': content.section_key,
                'section_name': content.section_name,
                'content': content.content,
                'is_active': content.is_active
            })
        except HomePageContent.DoesNotExist:
            return Response(
                {'error': 'Content section not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Return all active sections
        contents = HomePageContent.objects.filter(is_active=True).order_by('order', 'section_name')
        result = {}
        for content in contents:
            result[content.section_key] = {
                'section_name': content.section_name,
                'content': content.content,
                'is_active': content.is_active
            }
        return Response(result)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_bulk_order_page_content(request):
    """Get bulk order page content sections for public display"""
    from admin_api.models import BulkOrderPageContent
    
    section_key = request.query_params.get('section_key', None)
    
    if section_key:
        try:
            content = BulkOrderPageContent.objects.get(section_key=section_key, is_active=True)
            return Response({
                'section_key': content.section_key,
                'section_name': content.section_name,
                'content': content.content,
                'is_active': content.is_active
            })
        except BulkOrderPageContent.DoesNotExist:
            return Response(
                {'error': 'Content section not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Return all active sections
        contents = BulkOrderPageContent.objects.filter(is_active=True).order_by('order', 'section_name')
        result = {}
        for content in contents:
            result[content.section_key] = {
                'section_name': content.section_name,
                'content': content.content,
                'is_active': content.is_active
            }
        return Response(result)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_search_suggestions(request):
    """Get search suggestions based on query"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return Response([])
    
    # Get product suggestions
    products = Product.objects.filter(
        Q(title__icontains=query) |
        Q(category__name__icontains=query) |
        Q(subcategory__name__icontains=query),
        is_active=True
    ).values('title', 'slug', 'category__name')[:10]
    
    # Get category suggestions
    categories = Category.objects.filter(
        name__icontains=query,
        is_active=True
    ).values('name', 'slug')[:5]
    
    # Get subcategory suggestions
    subcategories = Subcategory.objects.filter(
        name__icontains=query,
        is_active=True
    ).values('name', 'slug', 'category__name')[:5]
    
    suggestions = []
    
    # Add product suggestions
    for product in products:
        suggestions.append({
            'type': 'product',
            'title': product['title'],
            'subtitle': product['category__name'],
            'slug': product['slug']
        })
    
    # Add category suggestions
    for category in categories:
        suggestions.append({
            'type': 'category',
            'title': category['name'],
            'subtitle': 'Category',
            'slug': category['slug']
        })
    
    # Add subcategory suggestions
    for subcategory in subcategories:
        suggestions.append({
            'type': 'subcategory',
            'title': subcategory['name'],
            'subtitle': f"in {subcategory['category__name']}",
            'slug': subcategory['slug']
        })
    
    return Response(suggestions[:15])  # Limit total suggestions


@api_view(['GET'])
@permission_classes([AllowAny])
def get_product_recommendations(request, slug):
    """Get product recommendations for a specific product"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # Get different types of recommendations
    buy_with = ProductRecommendation.objects.filter(
        product=product,
        recommendation_type='buy_with',
        is_active=True
    ).select_related('recommended_product')[:10]
    
    inspired_by = ProductRecommendation.objects.filter(
        product=product,
        recommendation_type='inspired_by',
        is_active=True
    ).select_related('recommended_product')[:10]
    
    frequently_viewed = ProductRecommendation.objects.filter(
        product=product,
        recommendation_type='frequently_viewed',
        is_active=True
    ).select_related('recommended_product')[:10]
    
    similar = ProductRecommendation.objects.filter(
        product=product,
        recommendation_type='similar',
        is_active=True
    ).select_related('recommended_product')[:10]
    
    recommended = ProductRecommendation.objects.filter(
        product=product,
        recommendation_type='recommended',
        is_active=True
    ).select_related('recommended_product')[:10]
    
    return Response({
        'buy_with': ProductListSerializer([rec.recommended_product for rec in buy_with], many=True).data,
        'inspired_by': ProductListSerializer([rec.recommended_product for rec in inspired_by], many=True).data,
        'frequently_viewed': ProductListSerializer([rec.recommended_product for rec in frequently_viewed], many=True).data,
        'similar': ProductListSerializer([rec.recommended_product for rec in similar], many=True).data,
        'recommended': ProductListSerializer([rec.recommended_product for rec in recommended], many=True).data,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_filter_options(request):
    """Get available filter options"""
    # Get base queryset
    queryset = Product.objects.filter(is_active=True)
    
    # Apply any existing filters
    filter_params = request.GET.copy()
    if 'category' in filter_params:
        queryset = queryset.filter(category__slug=filter_params['category'])
    if 'subcategory' in filter_params:
        queryset = queryset.filter(subcategory__slug=filter_params['subcategory'])
    
    # Get filter options
    filter_options = ProductAggregationFilter.get_filter_options(queryset)
    
    return Response(filter_options)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_brands(request):
    """Get list of active brands/vendors"""
    brands = Vendor.objects.filter(
        status='active',
        is_verified=True
    ).values('id', 'brand_name', 'business_name').order_by('brand_name', 'business_name')
    
    return Response(list(brands))


@api_view(['GET'])
@permission_classes([AllowAny])
def get_active_offers(request):
    """Get all products with active offers for advertisement boxes"""
    from django.utils import timezone
    
    now = timezone.now()
    
    # Get all products with active offers
    offers = ProductOffer.objects.filter(
        is_active=True
    ).filter(
        Q(valid_from__isnull=True) | Q(valid_from__lte=now),
        Q(valid_until__isnull=True) | Q(valid_until__gte=now)
    ).select_related('product').prefetch_related(
        'product__images'
    ).order_by('-created_at')
    
    # Serialize offers with product data
    serialized_offers = []
    for offer in offers:
        serialized_offers.append({
            'id': offer.id,
            'title': offer.title,
            'description': offer.description,
            'discount_percentage': offer.discount_percentage,
            'discount_amount': offer.discount_amount,
            'valid_from': offer.valid_from,
            'valid_until': offer.valid_until,
            'product': {
                'id': offer.product.id,
                'title': offer.product.title,
                'slug': offer.product.slug,
                'main_image': offer.product.main_image,
                'price': offer.product.price,
                'old_price': offer.product.old_price,
                'category': offer.product.category.name if offer.product.category else None
            }
        })
    
    return Response({
        'count': len(serialized_offers),
        'results': serialized_offers
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_offer(request):
    """Create a new product offer"""
    from rest_framework import status
    
    # Check if user is admin or staff
    if not (request.user.is_staff or request.user.is_superuser):
        return Response(
            {'error': 'You do not have permission to create offers.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    product_id = request.data.get('product_id')
    title = request.data.get('title')
    description = request.data.get('description', '')
    discount_percentage = request.data.get('discount_percentage')
    discount_amount = request.data.get('discount_amount')
    is_active = request.data.get('is_active', True)
    valid_from = request.data.get('valid_from')
    valid_until = request.data.get('valid_until')
    
    # Validation
    if not product_id:
        return Response(
            {'error': 'product_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not title:
        return Response(
            {'error': 'title is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Create the offer
    offer = ProductOffer.objects.create(
        product=product,
        title=title,
        description=description,
        discount_percentage=discount_percentage,
        discount_amount=discount_amount,
        is_active=is_active,
        valid_from=valid_from,
        valid_until=valid_until
    )
    
    # Serialize the created offer
    serializer = ProductOfferSerializer(offer)
    return Response({
        'message': 'Offer created successfully',
        'offer': serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_browsing_history(request):
    """Track when a user views a product"""
    product_id = request.data.get('product_id')
    
    if not product_id:
        return Response(
            {'error': 'product_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get or create browsing history entry
    browsing_history, created = BrowsingHistory.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={
            'category': product.category,
            'subcategory': product.subcategory,
        }
    )
    
    if not created:
        # Update view count and last viewed
        browsing_history.view_count += 1
        browsing_history.last_viewed = timezone.now()
        # Update category/subcategory if product changed
        if not browsing_history.category:
            browsing_history.category = product.category
        if not browsing_history.subcategory:
            browsing_history.subcategory = product.subcategory
        browsing_history.save()
    
    serializer = BrowsingHistorySerializer(browsing_history)
    return Response({
        'message': 'Browsing history tracked successfully',
        'data': serializer.data
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_browsing_history(request):
    """Get user's browsing history"""
    limit = int(request.query_params.get('limit', 20))
    
    browsing_history = BrowsingHistory.objects.filter(
        user=request.user
    ).select_related(
        'product', 'category', 'subcategory'
    ).prefetch_related(
        'product__images',
        'product__variants__color'
    ).order_by('-last_viewed')[:limit]
    
    serializer = BrowsingHistorySerializer(browsing_history, many=True)
    return Response({
        'count': len(serializer.data),
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_browsed_categories(request):
    """Get categories based on user's browsing history"""
    # Get unique categories from browsing history, ordered by most recently browsed
    from django.db.models import Count, Max
    
    categories_data = BrowsingHistory.objects.filter(
        user=request.user,
        category__isnull=False
    ).values(
        'category_id', 'category__name', 'category__slug', 
        'category__image', 'category__description'
    ).annotate(
        product_count=Count('product_id', distinct=True),
        last_viewed=Max('last_viewed')
    ).order_by('-last_viewed', '-product_count')
    
    # Convert to list with proper structure
    categories = []
    for cat_data in categories_data:
        # Get product count for this category
        category = Category.objects.get(id=cat_data['category_id'])
        total_products = category.products.filter(is_active=True).count()
        
        categories.append({
            'id': cat_data['category_id'],
            'name': cat_data['category__name'],
            'slug': cat_data['category__slug'],
            'image': cat_data['category__image'],
            'description': cat_data['category__description'],
            'product_count': total_products,
            'browsed_product_count': cat_data['product_count']
        })
    
    return Response({
        'count': len(categories),
        'results': categories
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_browsing_history(request):
    """Clear user's browsing history"""
    product_id = request.query_params.get('product_id')
    
    if product_id:
        # Clear specific product from history
        deleted_count, _ = BrowsingHistory.objects.filter(
            user=request.user,
            product_id=product_id
        ).delete()
        
        return Response({
            'message': f'Removed {deleted_count} item(s) from browsing history'
        })
    else:
        # Clear all browsing history
        deleted_count, _ = BrowsingHistory.objects.filter(
            user=request.user
        ).delete()
        
        return Response({
            'message': f'Cleared {deleted_count} item(s) from browsing history'
        })