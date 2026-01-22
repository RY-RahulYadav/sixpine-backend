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
    ProductFeature, ProductOffer, BrowsingHistory, Discount, Wishlist,
    NavbarCategory, NavbarSubcategory
)
from accounts.models import Vendor
from .serializers import (
    ProductListSerializer, ProductDetailSerializer, ProductSearchSerializer,
    CategorySerializer, SubcategorySerializer, ColorSerializer, MaterialSerializer,
    ProductReviewSerializer, ProductFilterSerializer, ProductOfferSerializer,
    BrowsingHistorySerializer, WishlistSerializer, WishlistCreateSerializer,
    NavbarCategorySerializer
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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'short_description', 'category__name', 'subcategory__name', 'brand', 'material']
    
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
            from django.db.models import Case, When, IntegerField, Min, Q
            # Get the current sort option to preserve it within priority groups
            sort_option = request.query_params.get('sort', 'relevance')
            
            # For price sorting, ensure annotation is present (it should be from get_queryset, but ensure it)
            if sort_option in ['price_low_to_high', 'price_high_to_low']:
                # Check if annotation already exists in queryset annotations
                if 'min_variant_price' not in queryset.query.annotations:
                    queryset = queryset.annotate(
                        min_variant_price=Min('variants__price', filter=Q(variants__is_active=True))
                    )
                if sort_option == 'price_low_to_high':
                    sort_field = 'min_variant_price'
                else:
                    sort_field = '-min_variant_price'
            else:
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
        
        # Always expand variants into separate items by default
        # Allow disabling with expand_variants=false if needed
        expand_variants = request.query_params.get('expand_variants', 'true').lower() != 'false'
        
        # Get filter options for the current queryset
        filter_options = ProductAggregationFilter.get_filter_options(queryset)
        
        # If expand_variants, we need to handle pagination differently
        if expand_variants:
            # Get subcategory filter if present
            subcategory_param = request.query_params.get('subcategory')
            subcategory_name = None
            subcategory_id = None
            if subcategory_param:
                # Try to get subcategory by slug to get the name and ID
                try:
                    subcategory = Subcategory.objects.get(slug=subcategory_param, is_active=True)
                    subcategory_name = subcategory.name
                    subcategory_id = subcategory.id
                except Subcategory.DoesNotExist:
                    # If not found, use the param as-is (might be a name)
                    subcategory_name = subcategory_param.replace('-', ' ')
            
            # Get price range filters if present
            min_price = request.query_params.get('min_price')
            max_price = request.query_params.get('max_price')
            min_price_float = float(min_price) if min_price else None
            max_price_float = float(max_price) if max_price else None
            
            # Get color filter if present
            color_param = request.query_params.get('color')
            selected_colors = []
            if color_param:
                # Handle comma-separated color names
                selected_colors = [c.strip() for c in color_param.split(',') if c.strip()]
            
            # Get discount filter if present
            min_discount_param = request.query_params.get('min_discount')
            min_discount_float = float(min_discount_param) if min_discount_param else None
            
            # Get rating filter if present
            min_rating_param = request.query_params.get('min_rating')
            min_rating_float = float(min_rating_param) if min_rating_param else None
            
            # Expand variants: create a list where each variant is a separate item
            expanded_results = []
            seen_variant_ids = set()  # Track variant IDs to prevent duplicates
            for product in queryset:
                # Prefetch variants with their subcategories and images for better performance
                # Use Prefetch to ensure subcategories are loaded correctly
                variants = product.variants.filter(is_active=True).prefetch_related(
                    'images',
                    Prefetch('subcategories', queryset=Subcategory.objects.filter(is_active=True))
                ).all()
                if variants.exists():
                    # If product has variants, add each variant as a separate item
                    for variant in variants:
                        # Filter by color if specified
                        if selected_colors:
                            variant_color_name = variant.color.name if variant.color else ''
                            # Check if variant color matches any selected color (case-insensitive)
                            color_matches = any(
                                variant_color_name.lower() == selected_color.lower() 
                                for selected_color in selected_colors
                            )
                            if not color_matches:
                                continue
                        
                        # Filter by price range if specified
                        variant_price = float(variant.price) if variant.price else 0
                        if min_price_float is not None and variant_price < min_price_float:
                            continue
                        if max_price_float is not None and variant_price > max_price_float:
                            continue
                        
                        # Filter by discount percentage if specified
                        if min_discount_float is not None:
                            # Calculate discount percentage for this variant
                            variant_discount = 0
                            # First check if variant has discount_percentage field set
                            if variant.discount_percentage:
                                variant_discount = float(variant.discount_percentage)
                            # Otherwise calculate from old_price and price
                            elif variant.old_price and variant.price and float(variant.old_price) > 0:
                                variant_discount = ((float(variant.old_price) - float(variant.price)) / float(variant.old_price)) * 100
                            
                            # Round discount to avoid floating point comparison issues
                            variant_discount = round(variant_discount, 2)
                            
                            # Only include variants with discount >= min_discount
                            # Use >= comparison to include variants that meet or exceed the threshold
                            if variant_discount < min_discount_float:
                                continue
                        
                        # Filter by rating if specified
                        if min_rating_float is not None:
                            # Get average rating for the product
                            from django.db.models import Avg
                            avg_rating = product.reviews.filter(is_approved=True).aggregate(
                                avg_rating=Avg('rating')
                            )['avg_rating']
                            product_rating = round(float(avg_rating), 1) if avg_rating else 0.0
                            
                            # Only include variants from products with rating >= min_rating
                            if product_rating < min_rating_float:
                                continue
                        # Filter variants by subcategory: if subcategory filter is set, only include variants that have this subcategory
                        # If subcategory is "Sofa Set" or similar, show all variants
                        if subcategory_name and subcategory_name.lower() not in ['sofa set', 'sofa sets', 'set']:
                            # Check if variant has this subcategory in its subcategories ManyToMany
                            variant_has_subcategory = False
                            if subcategory_id:
                                # Use subcategory ID (most reliable method)
                                # Get all subcategory IDs for this variant
                                variant_subcategory_ids = list(variant.subcategories.values_list('id', flat=True))
                                if subcategory_id in variant_subcategory_ids:
                                    variant_has_subcategory = True
                            else:
                                # Fallback: check by name (case-insensitive)
                                if hasattr(variant, 'subcategories') and variant.subcategories.exists():
                                    variant_subcategory_names = [sub.name.lower() for sub in variant.subcategories.all()]
                                    if subcategory_name.lower() in variant_subcategory_names:
                                        variant_has_subcategory = True
                            
                            # If variant doesn't have this subcategory, skip it
                            if not variant_has_subcategory:
                                continue
                        
                        # Skip if this variant has already been added (prevent duplicates)
                        # Check this AFTER subcategory filtering to ensure we only mark variants as seen if they're actually added
                        if variant.id in seen_variant_ids:
                            continue
                        seen_variant_ids.add(variant.id)
                        # If no subcategory filter or it's a "set", include all variants
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
                        
                        # Determine main image: prioritize variant.image field, then first variant image, then product main_image
                        # variant.image is the designated main image set by admin
                        main_image_url = (
                            variant.image if variant.image 
                            else variant_images[0]['image'] if variant_images 
                            else product.main_image
                        )
                        
                        expanded_results.append({
                            'id': f"{product.id}-{variant.id}",  # Unique ID for variant
                            'product_id': product.id,
                            'variant_id': variant.id,
                            'title': f"{product.title} - {variant.title}",  # Include variant title in product title
                            'slug': product.slug,
                            'product_title': product.title,  # Original product title
                            'short_description': product.short_description,
                            'main_image': main_image_url,
                            'images': variant_images if variant_images else [{'image': variant.image if variant.image else product.main_image}] if variant.image or product.main_image else [],
                            'price': float(variant.price) if variant.price else float(product.price),
                            'old_price': float(variant.old_price) if variant.old_price else (float(product.old_price) if product.old_price else None),
                            'is_on_sale': bool(variant.old_price and variant.price and float(variant.old_price) > float(variant.price)),
                            'discount_percentage': int(variant.discount_percentage) if variant.discount_percentage else (
                                int(round(((float(variant.old_price) - float(variant.price)) / float(variant.old_price) * 100), 0)) 
                                if variant.old_price and variant.price and float(variant.old_price) > 0 and float(variant.old_price) > float(variant.price) 
                                else 0
                            ),
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
                            'subcategories': [{
                                'id': sub.id,
                                'name': sub.name,
                                'slug': sub.slug
                            } for sub in product.subcategories.filter(is_active=True)] if hasattr(product, 'subcategories') else [],
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
                                'quality': variant.quality,
                                'price': float(variant.price) if variant.price else None,
                                'old_price': float(variant.old_price) if variant.old_price else None,
                                'stock_quantity': variant.stock_quantity,
                                'is_in_stock': variant.is_in_stock,
                                'image': main_image_url,  # Use same main_image logic
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
            
            # Filter expanded results by search query if present (to match variant titles)
            search_query = request.query_params.get('q') or request.query_params.get('search')
            if search_query:
                import re
                # Filter expanded results to only include variants that match the search
                # Check if search matches product title, variant title, or other fields
                filtered_results = []
                for item in expanded_results:
                    # Check if search matches in any of these fields
                    matches = False
                    try:
                        # Try regex matching on title (product + variant title combined)
                        if re.search(search_query, item.get('title', ''), re.IGNORECASE):
                            matches = True
                        # Also check variant title separately
                        elif item.get('variant') and item['variant'].get('title'):
                            if re.search(search_query, item['variant']['title'], re.IGNORECASE):
                                matches = True
                        # Check product title
                        elif item.get('product_title'):
                            if re.search(search_query, item['product_title'], re.IGNORECASE):
                                matches = True
                        # Check other fields (case-insensitive contains)
                        elif search_query.lower() in (item.get('short_description', '') or '').lower():
                            matches = True
                        elif item.get('brand') and search_query.lower() in item['brand'].lower():
                            matches = True
                    except re.error:
                        # If regex is invalid, fall back to simple contains
                        search_lower = search_query.lower()
                        if search_lower in (item.get('title', '') or '').lower():
                            matches = True
                        elif item.get('variant') and item['variant'].get('title'):
                            if search_lower in item['variant']['title'].lower():
                                matches = True
                        elif item.get('product_title'):
                            if search_lower in item['product_title'].lower():
                                matches = True
                        elif search_lower in (item.get('short_description', '') or '').lower():
                            matches = True
                        elif item.get('brand') and search_lower in item['brand'].lower():
                            matches = True
                    
                    if matches:
                        filtered_results.append(item)
                expanded_results = filtered_results
            
            # Apply sorting to expanded results
            sort_option = request.query_params.get('sort', 'relevance')
            expanded_results = self._sort_expanded_results(expanded_results, sort_option)
            
            # Shuffle results for variety (only if sort is relevance)
            if sort_option == 'relevance':
                import random
                random.shuffle(expanded_results)
            
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
            'features',
            'offers',
            'reviews',
            Prefetch('variants', queryset=ProductVariant.objects.filter(is_active=True).select_related('color').prefetch_related('images', 'specifications')),
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


class NavbarCategoryListView(generics.ListAPIView):
    """List navbar categories with subcategories for main site navigation"""
    serializer_class = NavbarCategorySerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return NavbarCategory.objects.filter(is_active=True).prefetch_related(
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
    
    def create(self, request, *args, **kwargs):
        """Override create to handle duplicate reviews and file uploads"""
        product_slug = self.kwargs.get('slug')
        product = get_object_or_404(Product, slug=product_slug)
        
        # Handle file uploads to Cloudinary
        attachments = []
        if request.FILES:
            try:
                import cloudinary.uploader
                
                for key, file in request.FILES.items():
                    if key.startswith('attachment_'):
                        # Determine resource type based on file type
                        file_type = file.content_type
                        resource_type = 'auto'  # Cloudinary will auto-detect
                        
                        if file_type.startswith('image/'):
                            resource_type = 'image'
                        elif file_type == 'application/pdf':
                            resource_type = 'raw'
                        elif file_type.startswith('video/'):
                            resource_type = 'video'
                        
                        # Prepare transformations for images only
                        upload_params = {
                            'folder': 'review_attachments',
                            'resource_type': resource_type
                        }
                        
                        # Add watermark and WebP format for images
                        if resource_type == 'image':
                            upload_params['transformation'] = [
                                {
                                    'fetch_format': 'webp',
                                    'quality': 'auto',
                                    'overlay': 'watermarks:sixpine_watermark',
                                    'opacity': 70,  # Higher opacity (70%) for more visible watermark protection
                                    'angle': -45,
                                    'flags': 'tiled',
                                    'width': 600,
                                    'height': 600,
                                    'gravity': 'center'
                                }
                            ]
                        
                        # Upload to Cloudinary
                        upload_result = cloudinary.uploader.upload(
                            file,
                            **upload_params
                        )
                        
                        attachments.append({
                            'url': upload_result['secure_url'],
                            'public_id': upload_result.get('public_id', ''),
                            'type': resource_type,
                            'name': file.name,
                            'size': file.size,
                            'mime_type': file_type
                        })
            except Exception as e:
                return Response(
                    {'error': f'File upload failed: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Prepare data for serializer (exclude file fields)
        # Convert QueryDict to regular dict for proper JSON handling
        data = dict(request.data.items())
        # Remove file keys from data
        data = {k: v for k, v in data.items() if not k.startswith('attachment_')}
        
        # Allow users to add multiple reviews - don't check for existing reviews
        # Create new review - requires approval
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        # Extract reviewer_name from validated data
        reviewer_name = serializer.validated_data.pop('reviewer_name', '')
        # Save the review first
        review = serializer.save(product=product, user=request.user, is_approved=False, reviewer_name=reviewer_name)
        # Then set attachments directly (bypassing serializer for JSON field)
        if attachments:
            review.attachments = attachments
            review.save(update_fields=['attachments'])
        # Refresh from DB to get attachments in response
        review.refresh_from_db()
        response_serializer = self.get_serializer(review)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        # This method is overridden in create() method, so it won't be called
        # But keeping it for compatibility
        product_slug = self.kwargs.get('slug')
        product = get_object_or_404(Product, slug=product_slug)
        # New reviews require approval - set is_approved=False
        serializer.save(product=product, user=self.request.user, is_approved=False)


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
    """Get homepage content sections for public display with enriched product data"""
    from admin_api.models import HomePageContent
    
    def enrich_product_data(content_data):
        """Enrich product data with latest database values including parent_main_image"""
        if not isinstance(content_data, dict):
            return content_data
        
        enriched_data = content_data.copy()
        
        # Process products in discover/topRated sections
        for section_key in ['discover', 'topRated']:
            if section_key in enriched_data and 'products' in enriched_data[section_key]:
                products = enriched_data[section_key]['products']
                if isinstance(products, list):
                    for product in products:
                        if isinstance(product, dict) and 'productId' in product:
                            try:
                                db_product = Product.objects.get(id=product['productId'])
                                first_variant = db_product.variants.filter(is_active=True).first()
                                
                                # Update image with priority: parent_main_image > variant.image > product.main_image
                                if db_product.parent_main_image:
                                    product['image'] = db_product.parent_main_image
                                    product['img'] = db_product.parent_main_image
                                    product['parent_main_image'] = db_product.parent_main_image
                                elif first_variant and first_variant.image:
                                    product['image'] = first_variant.image
                                    product['img'] = first_variant.image
                                elif db_product.main_image:
                                    product['image'] = db_product.main_image
                                    product['img'] = db_product.main_image
                                # Populate price fields from first active variant or fallback to product
                                try:
                                    product['price'] = float(first_variant.price) if first_variant and first_variant.price else (float(db_product.price) if db_product.price else None)
                                except Exception:
                                    product['price'] = None
                                try:
                                    product['old_price'] = float(first_variant.old_price) if first_variant and first_variant.old_price else (float(db_product.old_price) if db_product.old_price else None)
                                except Exception:
                                    product['old_price'] = None
                            except Product.DoesNotExist:
                                pass
        
        # Process slider products
        for slider_key in ['slider1Products', 'slider2Products']:
            if slider_key in enriched_data and isinstance(enriched_data[slider_key], list):
                for product in enriched_data[slider_key]:
                    if isinstance(product, dict) and 'productId' in product:
                        try:
                            db_product = Product.objects.get(id=product['productId'])
                            first_variant = db_product.variants.filter(is_active=True).first()
                            
                            # Update image with priority
                            if db_product.parent_main_image:
                                product['img'] = db_product.parent_main_image
                                product['image'] = db_product.parent_main_image
                                product['parent_main_image'] = db_product.parent_main_image
                            elif first_variant and first_variant.image:
                                product['img'] = first_variant.image
                                product['image'] = first_variant.image
                            elif db_product.main_image:
                                product['img'] = db_product.main_image
                                product['image'] = db_product.main_image
                            # Populate price fields from first active variant or fallback to product
                            try:
                                product['price'] = float(first_variant.price) if first_variant and first_variant.price else (float(db_product.price) if db_product.price else None)
                            except Exception:
                                product['price'] = None
                            try:
                                product['old_price'] = float(first_variant.old_price) if first_variant and first_variant.old_price else (float(db_product.old_price) if db_product.old_price else None)
                            except Exception:
                                product['old_price'] = None
                        except Product.DoesNotExist:
                            pass
        
        # Process trending products
        if 'trendingProducts' in enriched_data and isinstance(enriched_data['trendingProducts'], list):
            for product in enriched_data['trendingProducts']:
                if isinstance(product, dict) and 'productId' in product:
                    try:
                        db_product = Product.objects.get(id=product['productId'])
                        first_variant = db_product.variants.filter(is_active=True).first()
                        
                        if db_product.parent_main_image:
                            product['image'] = db_product.parent_main_image
                            product['parent_main_image'] = db_product.parent_main_image
                        elif first_variant and first_variant.image:
                            product['image'] = first_variant.image
                        elif db_product.main_image:
                            product['image'] = db_product.main_image
                        # Populate price fields from first active variant or fallback to product
                        try:
                            product['price'] = float(first_variant.price) if first_variant and first_variant.price else (float(db_product.price) if db_product.price else None)
                        except Exception:
                            product['price'] = None
                        try:
                            product['old_price'] = float(first_variant.old_price) if first_variant and first_variant.old_price else (float(db_product.old_price) if db_product.old_price else None)
                        except Exception:
                            product['old_price'] = None
                    except Product.DoesNotExist:
                        pass
        
        # Process daily deals
        if 'deals' in enriched_data and isinstance(enriched_data['deals'], list):
            for deal in enriched_data['deals']:
                if isinstance(deal, dict) and 'productId' in deal:
                    try:
                        db_product = Product.objects.get(id=deal['productId'])
                        first_variant = db_product.variants.filter(is_active=True).first()
                        
                        if db_product.parent_main_image:
                            deal['image'] = db_product.parent_main_image
                            deal['parent_main_image'] = db_product.parent_main_image
                        elif first_variant and first_variant.image:
                            deal['image'] = first_variant.image
                        elif db_product.main_image:
                            deal['image'] = db_product.main_image
                        # Populate price fields from first active variant or fallback to product
                        try:
                            deal['price'] = float(first_variant.price) if first_variant and first_variant.price else (float(db_product.price) if db_product.price else None)
                        except Exception:
                            deal['price'] = None
                        try:
                            deal['old_price'] = float(first_variant.old_price) if first_variant and first_variant.old_price else (float(db_product.old_price) if db_product.old_price else None)
                        except Exception:
                            deal['old_price'] = None
                    except Product.DoesNotExist:
                        pass
        
        # Process generic products array (used in trending, best deals, and other pages)
        if 'products' in enriched_data and isinstance(enriched_data['products'], list):
            for product in enriched_data['products']:
                if isinstance(product, dict) and 'productId' in product:
                    try:
                        db_product = Product.objects.get(id=product['productId'])
                        first_variant = db_product.variants.filter(is_active=True).first()
                        
                        if db_product.parent_main_image:
                            product['image'] = db_product.parent_main_image
                            product['parent_main_image'] = db_product.parent_main_image
                        elif first_variant and first_variant.image:
                            product['image'] = first_variant.image
                        elif db_product.main_image:
                            product['image'] = db_product.main_image
                        # Populate price fields from first active variant or fallback to product
                        try:
                            product['price'] = float(first_variant.price) if first_variant and first_variant.price else (float(db_product.price) if db_product.price else None)
                        except Exception:
                            product['price'] = None
                        try:
                            product['old_price'] = float(first_variant.old_price) if first_variant and first_variant.old_price else (float(db_product.old_price) if db_product.old_price else None)
                        except Exception:
                            product['old_price'] = None
                    except Product.DoesNotExist:
                        pass
        
        return enriched_data
    
    section_key = request.query_params.get('section_key', None)
    
    if section_key:
        try:
            content = HomePageContent.objects.get(section_key=section_key, is_active=True)
            enriched_content = enrich_product_data(content.content)
            return Response({
                'section_key': content.section_key,
                'section_name': content.section_name,
                'content': enriched_content,
                'is_active': content.is_active
            })
        except HomePageContent.DoesNotExist:
            return Response(
                {'error': 'Content section not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Return all active sections with enriched data
        contents = HomePageContent.objects.filter(is_active=True).order_by('order', 'section_name')
        result = {}
        for content in contents:
            enriched_content = enrich_product_data(content.content)
            result[content.section_key] = {
                'section_name': content.section_name,
                'content': enriched_content,
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
def get_faq_page_content(request):
    """Get FAQ page content sections for public display"""
    from admin_api.models import FAQPageContent
    
    section_key = request.query_params.get('section_key', None)
    
    if section_key:
        try:
            content = FAQPageContent.objects.get(section_key=section_key, is_active=True)
            return Response({
                'section_key': content.section_key,
                'section_name': content.section_name,
                'content': content.content,
                'is_active': content.is_active
            })
        except FAQPageContent.DoesNotExist:
            return Response(
                {'error': 'Content section not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Return all active sections
        contents = FAQPageContent.objects.filter(is_active=True).order_by('order', 'section_name')
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
def get_active_advertisements(request):
    """Get active advertisements for product detail pages"""
    from admin_api.models import Advertisement
    from django.utils import timezone
    
    now = timezone.now()
    
    # Get all advertisements (for debugging)
    all_ads = Advertisement.objects.all()
    
    # Get all valid active advertisements
    # Filter: is_active=True AND (valid_from is null or <= now) AND (valid_until is null or >= now)
    advertisements = Advertisement.objects.filter(
        is_active=True
    ).filter(
        Q(valid_from__isnull=True) | Q(valid_from__lte=now),
        Q(valid_until__isnull=True) | Q(valid_until__gte=now)
    ).order_by('display_order', '-created_at')
    
    # Debug: Log total ads and filtered ads
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Total advertisements in DB: {all_ads.count()}")
    logger.info(f"Active advertisements after filter: {advertisements.count()}")
    
    # If no ads found with strict filter, try showing ads that are just marked active
    # (ignore date constraints if they're causing issues)
    if advertisements.count() == 0:
        # Fallback: show ads that are just marked as active, regardless of dates
        advertisements = Advertisement.objects.filter(
            is_active=True
        ).order_by('display_order', '-created_at')
        logger.info(f"Fallback: Found {advertisements.count()} active ads (ignoring date constraints)")
    
    # Serialize advertisements
    serialized_ads = []
    for ad in advertisements:
        serialized_ads.append({
            'id': ad.id,
            'title': ad.title,
            'description': ad.description,
            'image': str(ad.image) if ad.image else '',
            'button_text': ad.button_text,
            'button_link': ad.button_link,
            'discount_percentage': ad.discount_percentage,
        })
    
    return Response({
        'count': len(serialized_ads),
        'results': serialized_ads
    })


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
    
    brands_list = list(brands)
    
    # Add Sixpine as a special brand option (vendor=None)
    brands_list.insert(0, {
        'id': 0,  # Use 0 as special ID for Sixpine
        'brand_name': 'Sixpine',
        'business_name': 'Sixpine'
    })
    
    return Response(brands_list)


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
        # Get price from first active variant
        first_variant = offer.product.variants.filter(is_active=True).first()
        price = float(first_variant.price) if first_variant and first_variant.price else None
        old_price = float(first_variant.old_price) if first_variant and first_variant.old_price else None
        
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
                'price': price,
                'old_price': old_price,
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


# ==================== Wishlist Views ====================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def wishlist_view(request):
    """Get wishlist (GET) or add to wishlist (POST)"""
    if request.method == 'GET':
        """Get user's wishlist"""
        try:
            wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product').order_by('-added_at')
            serializer = WishlistSerializer(wishlist_items, many=True)
            
            return Response({
                'count': wishlist_items.count(),
                'results': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'Failed to fetch wishlist: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif request.method == 'POST':
        """Add product to wishlist"""
        try:
            serializer = WishlistCreateSerializer(data=request.data)
            if serializer.is_valid():
                product_id = serializer.validated_data['product_id']
                product = Product.objects.get(id=product_id, is_active=True)
                
                # Check if already in wishlist
                wishlist_item, created = Wishlist.objects.get_or_create(
                    user=request.user,
                    product=product
                )
                
                if created:
                    wishlist_serializer = WishlistSerializer(wishlist_item)
                    return Response({
                        'message': 'Product added to wishlist',
                        'data': wishlist_serializer.data
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'message': 'Product already in wishlist',
                        'data': WishlistSerializer(wishlist_item).data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response({
                'error': 'Product not found or inactive'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Failed to add to wishlist: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_wishlist(request, id):
    """Remove product from wishlist"""
    try:
        wishlist_item = Wishlist.objects.get(id=id, user=request.user)
        wishlist_item.delete()
        
        return Response({
            'message': 'Product removed from wishlist'
        }, status=status.HTTP_200_OK)
    except Wishlist.DoesNotExist:
        return Response({
            'error': 'Wishlist item not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to remove from wishlist: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_wishlist(request):
    """Toggle wishlist item: add if not exists, remove if exists. Returns current state."""
    try:
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({
                'error': 'product_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({
                'error': 'Product not found or inactive'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Try to find existing wishlist item
        wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
        
        if wishlist_item:
            # Remove from wishlist
            wishlist_item.delete()
            return Response({
                'message': 'Product removed from wishlist',
                'is_in_wishlist': False,
                'action': 'removed'
            }, status=status.HTTP_200_OK)
        else:
            # Add to wishlist
            wishlist_item = Wishlist.objects.create(user=request.user, product=product)
            serializer = WishlistSerializer(wishlist_item)
            return Response({
                'message': 'Product added to wishlist',
                'is_in_wishlist': True,
                'action': 'added',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response({
            'error': f'Failed to toggle wishlist: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_wishlist_by_product(request, product_id):
    """Remove product from wishlist by product_id (more efficient than fetching entire wishlist)"""
    try:
        wishlist_item = Wishlist.objects.filter(user=request.user, product_id=product_id).first()
        if wishlist_item:
            wishlist_item.delete()
            return Response({
                'message': 'Product removed from wishlist'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Product not in wishlist'
            }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to remove from wishlist: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_footer_settings(request):
    """Get footer settings (phone number, social media links, and app store URLs) for public display"""
    from admin_api.models import GlobalSettings
    
    settings_map = {}
    setting_keys = ['footer_phone_number', 'footer_linkedin_url', 'footer_twitter_url', 'footer_instagram_url', 'ios_app_url', 'android_app_url']
    
    for key in setting_keys:
        try:
            setting = GlobalSettings.objects.get(key=key)
            settings_map[key] = setting.value
        except GlobalSettings.DoesNotExist:
            settings_map[key] = ''
    
    return Response(settings_map)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_theme_colors(request):
    """Get theme colors for public display (no authentication required)"""
    from admin_api.models import GlobalSettings
    
    # Theme color keys
    theme_keys = [
        'header_bg_color', 'header_text_color',
        'subnav_bg_color', 'subnav_text_color',
        'category_tabs_bg_color', 'category_tabs_text_color',
        'footer_bg_color', 'footer_text_color',
        'back_to_top_bg_color', 'back_to_top_text_color',
        'buy_button_bg_color', 'buy_button_text_color',
        'cart_icon_color', 'wishlist_icon_color', 'wishlist_icon_inactive_color',
        'logo_url'
    ]
    
    settings_map = {}
    for key in theme_keys:
        try:
            setting = GlobalSettings.objects.get(key=key)
            settings_map[key] = setting.value
        except GlobalSettings.DoesNotExist:
            # Return empty string for missing settings (frontend will use defaults)
            settings_map[key] = ''
    
    return Response(settings_map)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_all_user_data(request):
    """Clear all user data: browsing history, wishlist, and browsed categories"""
    try:
        # Clear browsing history (this also clears browsed categories since they're derived from it)
        browsing_count, _ = BrowsingHistory.objects.filter(user=request.user).delete()
        
        # Clear wishlist
        wishlist_count, _ = Wishlist.objects.filter(user=request.user).delete()
        
        return Response({
            'message': 'All data cleared successfully',
            'browsing_history_deleted': browsing_count,
            'wishlist_deleted': wishlist_count,
            'total_deleted': browsing_count + wishlist_count
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'Failed to clear all data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_site_settings(request):
    """Get site settings for public display (right-click protection, etc.)"""
    from admin_api.models import GlobalSettings
    
    # Site settings keys
    setting_keys = [
        'right_click_protection_enabled',
    ]
    
    settings_map = {}
    for key in setting_keys:
        try:
            setting = GlobalSettings.objects.get(key=key)
            # Convert string 'true'/'false' to boolean for boolean settings
            value = setting.value
            if value.lower() == 'true':
                settings_map[key] = True
            elif value.lower() == 'false':
                settings_map[key] = False
            else:
                settings_map[key] = value
        except GlobalSettings.DoesNotExist:
            # Default values for settings
            if key == 'right_click_protection_enabled':
                settings_map[key] = True  # Default to enabled
            else:
                settings_map[key] = ''
    
    return Response(settings_map)