from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q, F, DecimalField
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .permissions import IsVendorUser
from admin_api.serializers import (
    AdminProductListSerializer, AdminProductDetailSerializer,
    AdminOrderListSerializer, AdminOrderDetailSerializer, AdminCouponSerializer,
    SellerOrderListSerializer
)
from products.models import (
    Product, ProductImage,
    ProductVariant, ProductVariantImage, ProductSpecification, ProductFeature, Coupon
)
from orders.models import Order, OrderItem
from accounts.models import Vendor, User


# ==================== Dashboard Views ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVendorUser])
def seller_dashboard_stats(request):
    """Get vendor-specific dashboard statistics"""
    vendor = request.user.vendor_profile
    
    # Calculate date ranges
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # Vendor-specific stats
    vendor_products = Product.objects.filter(vendor=vendor)
    total_products = vendor_products.count()
    
    # Vendor orders (orders containing vendor's products)
    vendor_order_items = OrderItem.objects.filter(vendor=vendor)
    vendor_orders = Order.objects.filter(items__vendor=vendor).distinct()
    
    total_orders = vendor_orders.count()
    # Calculate total order value: sum of total_amount (including tax) for orders containing vendor's products
    # For each order, calculate vendor's share of the total amount customer paid
    total_order_value = Decimal('0.00')
    for order in vendor_orders:
        # Get vendor's items in this order
        vendor_items = order.items.filter(vendor=vendor)
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
    
    # Keep total_revenue for backward compatibility (sum of items without tax)
    total_revenue = vendor_order_items.aggregate(
        total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total'] or Decimal('0.00')
    
    # Order summary stats
    delivered_orders = vendor_orders.filter(status='delivered').count()
    cod_orders = vendor_orders.filter(payment_method='COD').count()
    online_payment_orders = total_orders - cod_orders
    
    # Low stock products (vendor's products) - use vendor's threshold
    low_stock_threshold = vendor.low_stock_threshold or 100
    low_stock_products = vendor_products.annotate(
        total_stock=Sum('variants__stock_quantity', filter=Q(variants__is_active=True))
    ).filter(total_stock__lt=low_stock_threshold, total_stock__isnull=False, is_active=True).count()
    
    # Recent orders (last 10)
    recent_orders = vendor_orders.order_by('-created_at')[:10].values(
        'id', 'order_id', 'status', 'total_amount', 'created_at'
    )
    recent_orders = [{
        **order,
        'customer_name': Order.objects.get(id=order['id']).user.get_full_name() or Order.objects.get(id=order['id']).user.username
    } for order in recent_orders]
    
    # Top selling products (vendor's products)
    top_products = vendor_order_items.values('product').annotate(
        sold=Sum('quantity'),
        revenue=Sum(F('price') * F('quantity'))
    ).order_by('-sold')[:10]
    
    top_selling_products = []
    for item in top_products:
        product = Product.objects.get(id=item['product'])
        revenue = item.get('revenue') or Decimal('0.00')
        top_selling_products.append({
            'id': product.id,
            'title': product.title,
            'sold': item['sold'],
            'revenue': float(revenue)
        })
    
    # Sales by day (last 30 days)
    sales_by_day = []
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        day_order_items = vendor_order_items.filter(order__created_at__date=date)
        revenue = day_order_items.aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or Decimal('0.00')
        orders_count = vendor_orders.filter(created_at__date=date).count()
        sales_by_day.append({
            'date': date.isoformat(),
            'revenue': float(revenue),
            'orders': orders_count
        })
    
    # Calculate seller's net revenue (order value - platform fee - tax) for delivered orders only
    # This is the seller's profit, not the platform's profit
    from admin_api.models import GlobalSettings
    delivered_vendor_orders = vendor_orders.filter(status='delivered')
    total_net_revenue = Decimal('0.00')
    tax_rate = Decimal(str(GlobalSettings.get_setting('tax_rate', '5.00')))
    
    # Calculate for each delivered order item
    delivered_vendor_order_items = vendor_order_items.filter(order__status='delivered')
    for order_item in delivered_vendor_order_items:
        item_subtotal = order_item.price * order_item.quantity
        order = order_item.order
        
        # Calculate vendor's share of platform fee
        order_total_items = order.items.aggregate(
            total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'] or Decimal('0.00')
        
        vendor_share_platform_fee = Decimal('0.00')
        vendor_share_tax = Decimal('0.00')
        
        if order_total_items > 0:
            # Vendor's share of platform fee = (vendor_items_value / order_total) * platform_fee
            vendor_share_platform_fee = (item_subtotal / order_total_items) * (order.platform_fee or Decimal('0.00'))
            
            # Tax is calculated on subtotal (before platform fee)
            order_subtotal = order.subtotal
            if order_subtotal > 0:
                vendor_share_tax = (item_subtotal / order_subtotal) * (order.tax_amount or Decimal('0.00'))
            else:
                # Fallback: calculate tax directly on vendor's item
                vendor_share_tax = (item_subtotal * tax_rate) / Decimal('100.00')
        
        # Seller's net revenue = item value - platform fee - tax
        net_revenue_item = item_subtotal - vendor_share_platform_fee - vendor_share_tax
        total_net_revenue += net_revenue_item
    
    data = {
        'total_orders': total_orders,
        'total_order_value': str(total_order_value),
        'total_revenue': str(total_revenue),  # Keep for backward compatibility
        'total_net_profit': str(total_net_revenue),  # Seller's net revenue (order value - fees - tax)
        'total_products': total_products,
        'delivered_orders_count': delivered_orders,
        'cod_orders_count': cod_orders,
        'online_payment_orders_count': online_payment_orders,
        'low_stock_products': low_stock_products,
        'recent_orders': list(recent_orders),
        'top_selling_products': top_selling_products,
        'sales_by_day': sales_by_day
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVendorUser])
def seller_brand_analytics(request):
    """Get comprehensive brand analytics for vendor"""
    try:
        vendor = request.user.vendor_profile
    except Exception as e:
        return Response(
            {'error': 'Vendor profile not found', 'detail': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculate date ranges
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # Vendor-specific data
    vendor_products = Product.objects.filter(vendor=vendor)
    vendor_order_items = OrderItem.objects.filter(vendor=vendor)
    vendor_orders = Order.objects.filter(items__vendor=vendor).distinct()
    
    # Order stats
    total_orders = vendor_orders.count()
    total_revenue = vendor_order_items.aggregate(
        total=Sum(F('price') * F('quantity'))
    )['total'] or Decimal('0.00')
    average_order_value = (total_revenue / total_orders) if total_orders > 0 else Decimal('0.00')
    
    # Orders by status
    orders_by_status = vendor_orders.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Orders by month
    orders_by_month_data = vendor_orders.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Calculate revenue per month
    orders_by_month = []
    for item in orders_by_month_data:
        month_start = item['month']
        month_orders = vendor_orders.filter(
            created_at__year=month_start.year,
            created_at__month=month_start.month
        )
        month_revenue = vendor_order_items.filter(
            order__created_at__year=month_start.year,
            order__created_at__month=month_start.month
        ).aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or Decimal('0.00')
        
        orders_by_month.append({
            'month': f"{month_start.year}-{str(month_start.month).zfill(2)}",
            'count': item['count'],
            'revenue': float(month_revenue)
        })
    
    # Payment methods - calculate revenue from vendor's order items
    payment_methods_data = vendor_orders.values('payment_method').annotate(
        count=Count('id')
    ).order_by('-count')
    
    payment_methods = []
    for item in payment_methods_data:
        method = item['payment_method'] or 'Unknown'
        method_orders = vendor_orders.filter(payment_method=item['payment_method'])
        method_revenue = vendor_order_items.filter(
            order__payment_method=item['payment_method']
        ).aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or Decimal('0.00')
        
        payment_methods.append({
            'method': method,
            'count': item['count'],
            'revenue': float(method_revenue)
        })
    
    # Product stats
    total_products = vendor_products.count()
    active_products = vendor_products.filter(is_active=True).count()
    low_stock_threshold = vendor.low_stock_threshold or 100
    low_stock_products = vendor_products.annotate(
        total_stock=Sum('variants__stock_quantity', filter=Q(variants__is_active=True))
    ).filter(total_stock__lt=low_stock_threshold, total_stock__isnull=False, is_active=True).count()
    
    # Top selling products
    top_selling = vendor_order_items.values('product').annotate(
        sold=Sum('quantity'),
        revenue=Sum(F('price') * F('quantity'))
    ).order_by('-sold')[:10]
    
    top_selling_products = []
    for item in top_selling:
        try:
            product = Product.objects.get(id=item['product'], vendor=vendor)
            revenue = item.get('revenue') or Decimal('0.00')
            top_selling_products.append({
                'id': product.id,
                'title': product.title,
                'sold': item['sold'],
                'revenue': float(revenue)
            })
        except Product.DoesNotExist:
            continue
    
    # Products by category
    products_by_category = vendor_products.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Customer stats (customers who ordered vendor's products)
    vendor_customers = User.objects.filter(
        orders__items__vendor=vendor
    ).distinct()
    
    total_customers = vendor_customers.count()
    active_customers = vendor_customers.filter(is_active=True).count()
    
    # New customers this month
    this_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_customers_this_month = vendor_customers.filter(date_joined__gte=this_month).count()
    
    # Customers by month
    customers_by_month_data = vendor_customers.annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    customers_by_month = [
        {
            'month': f"{item['month'].year}-{str(item['month'].month).zfill(2)}",
            'count': item['count']
        }
        for item in customers_by_month_data
    ]
    
    # Top customers (by order count and revenue for vendor's products)
    top_customers_data = vendor_order_items.values('order__user').annotate(
        orders=Count('order', distinct=True),
        total_spent=Sum(F('price') * F('quantity'))
    ).order_by('-total_spent')[:10]
    
    top_customers = []
    for item in top_customers_data:
        try:
            user = User.objects.get(id=item['order__user'])
            top_customers.append({
                'id': user.id,
                'name': user.get_full_name() or user.username,
                'orders': item['orders'],
                'total_spent': float(item['total_spent'] or Decimal('0.00'))
            })
        except User.DoesNotExist:
            continue
    
    try:
        data = {
            'order_stats': {
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'average_order_value': float(average_order_value),
                'orders_by_status': [
                    {'status': item['status'], 'count': item['count']}
                    for item in orders_by_status
                ],
                'orders_by_month': [
                    {
                        'month': item['month'],
                        'count': item['count'],
                        'revenue': float(item.get('revenue') or Decimal('0.00'))
                    }
                    for item in orders_by_month
                ],
                'payment_methods': payment_methods
            },
            'product_stats': {
                'total_products': total_products,
                'active_products': active_products,
                'low_stock_products': low_stock_products,
                'top_selling': top_selling_products,
                'products_by_category': [
                    {'category': item['category__name'] or 'Uncategorized', 'count': item['count']}
                    for item in products_by_category
                ]
            },
            'customer_stats': {
                'total_customers': total_customers,
                'active_customers': active_customers,
                'new_customers_this_month': new_customers_this_month,
                'top_customers': top_customers,
                'customers_by_month': [
                    {'month': item['month'], 'count': item['count']}
                    for item in customers_by_month
                ]
            }
        }
        
        return Response(data)
    except Exception as e:
        import traceback
        print(f"Error in seller_brand_analytics: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': 'Failed to generate analytics', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== Product Management Views ====================
class SellerProductViewSet(viewsets.ModelViewSet):
    """Seller viewset for product management (vendor's products only)"""
    permission_classes = [IsAuthenticated, IsVendorUser]
    serializer_class = AdminProductListSerializer
    
    def get_queryset(self):
        vendor = self.request.user.vendor_profile
        queryset = Product.objects.filter(vendor=vendor).select_related(
            'category', 'subcategory', 'vendor'
        ).prefetch_related(
            'images', 'variants', 'specifications', 'features'
        ).order_by('-created_at')
        
        search = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)
        subcategory = self.request.query_params.get('subcategory', None)
        is_active = self.request.query_params.get('is_active', None)
        is_featured = self.request.query_params.get('is_featured', None)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(sku__icontains=search) |
                Q(short_description__icontains=search)
            )
        if category:
            queryset = queryset.filter(category_id=category)
        if subcategory:
            queryset = queryset.filter(subcategory_id=subcategory)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')
        
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return AdminProductDetailSerializer
        return AdminProductListSerializer
    
    def perform_create(self, serializer):
        """Set vendor when creating product"""
        vendor = self.request.user.vendor_profile
        serializer.save(vendor=vendor)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle product active status"""
        product = self.get_object()
        product.is_active = not product.is_active
        product.save()
        serializer = self.get_serializer(product)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_featured(self, request, pk=None):
        """Toggle product featured status"""
        product = self.get_object()
        product.is_featured = not product.is_featured
        product.save()
        serializer = self.get_serializer(product)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """Update product variant stock"""
        product = self.get_object()
        variant_id = request.data.get('variant_id')
        quantity = request.data.get('quantity')
        
        if not variant_id or quantity is None:
            return Response(
                {'error': 'variant_id and quantity are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            variant = ProductVariant.objects.get(id=variant_id, product=product)
            variant.stock_quantity = quantity
            variant.is_in_stock = quantity > 0
            variant.save()
            
            serializer = self.get_serializer(product)
            return Response(serializer.data)
        except ProductVariant.DoesNotExist:
            return Response(
                {'error': 'Variant not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ==================== Order Management Views ====================
class SellerOrderViewSet(viewsets.ModelViewSet):
    """Seller viewset for order management (vendor's orders only)"""
    permission_classes = [IsAuthenticated, IsVendorUser]
    serializer_class = SellerOrderListSerializer
    http_method_names = ['get', 'post', 'patch', 'head', 'options']  # Allow PATCH for updates
    
    def get_queryset(self):
        vendor = self.request.user.vendor_profile
        # Get orders that contain vendor's products
        queryset = Order.objects.filter(items__vendor=vendor).distinct().select_related(
            'user', 'shipping_address'
        ).prefetch_related('items__product', 'items__variant', 'items__vendor').order_by('-created_at')
        
        status_filter = self.request.query_params.get('status', None)
        payment_status = self.request.query_params.get('payment_status', None)
        payment_method = self.request.query_params.get('payment_method', None)
        search = self.request.query_params.get('search', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminOrderDetailSerializer
        return SellerOrderListSerializer
    
    def get_serializer_context(self):
        """Add vendor to serializer context for vendor-specific calculations"""
        context = super().get_serializer_context()
        context['vendor'] = self.request.user.vendor_profile
        return context
    
    def update(self, request, *args, **kwargs):
        """Update order (vendor can update status and tracking)"""
        from orders.models import OrderStatusHistory
        
        order = self.get_object()
        vendor = request.user.vendor_profile
        
        # Verify order contains vendor's products
        if not order.items.filter(vendor=vendor).exists():
            return Response(
                {'error': 'Order does not contain your products'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow updating status and tracking_number for vendor's items
        new_status = request.data.get('status')
        tracking_number = request.data.get('tracking_number')
        notes = request.data.get('notes', '')
        
        if new_status:
            if new_status not in dict(Order.STATUS_CHOICES):
                return Response(
                    {'error': 'Invalid status'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            order.status = new_status
            
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                notes=notes,
                created_by=request.user
            )
        
        if tracking_number:
            order.tracking_number = tracking_number
        
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status (vendor can update their order items)"""
        from orders.models import OrderStatusHistory
        
        order = self.get_object()
        vendor = request.user.vendor_profile
        
        # Verify order contains vendor's products
        if not order.items.filter(vendor=vendor).exists():
            return Response(
                {'error': 'Order does not contain your products'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            notes=notes,
            created_by=request.user
        )
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_payment_status(self, request, pk=None):
        """Update order payment status (vendor can update payment status)"""
        from orders.models import OrderNote
        
        order = self.get_object()
        vendor = request.user.vendor_profile
        
        # Verify order contains vendor's products
        if not order.items.filter(vendor=vendor).exists():
            return Response(
                {'error': 'Order does not contain your products'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_payment_status = request.data.get('payment_status')
        notes = request.data.get('notes', '')
        
        if not new_payment_status:
            return Response(
                {'error': 'Payment status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate payment status
        valid_statuses = ['pending', 'paid', 'failed', 'refunded', 'partially_refunded']
        if new_payment_status not in valid_statuses:
            return Response(
                {'error': 'Invalid payment status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_payment_status = order.payment_status
        order.payment_status = new_payment_status
        order.save()
        
        # Create order note if provided
        if notes:
            OrderNote.objects.create(
                order=order,
                note=notes,
            created_by=request.user
        )
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)


# ==================== Coupon Management Views ====================
class SellerCouponViewSet(viewsets.ModelViewSet):
    """Seller viewset for coupon management (vendor's coupons only)"""
    permission_classes = [IsAuthenticated, IsVendorUser]
    serializer_class = AdminCouponSerializer
    
    def get_queryset(self):
        vendor = self.request.user.vendor_profile
        queryset = Coupon.objects.filter(vendor=vendor).order_by('-created_at')
        
        search = self.request.query_params.get('search', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    def perform_create(self, serializer):
        """Set vendor when creating coupon"""
        vendor = self.request.user.vendor_profile
        serializer.save(vendor=vendor)
    
    def perform_update(self, serializer):
        """Ensure vendor can only update their own coupons"""
        vendor = self.request.user.vendor_profile
        serializer.save(vendor=vendor)


# ==================== Shipment Settings Views ====================
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsVendorUser])
def seller_shipment_settings(request):
    """Get or update vendor shipment address"""
    vendor = request.user.vendor_profile
    
    if request.method == 'GET':
        return Response({
            'shipment_address': vendor.shipment_address or '',
            'shipment_city': vendor.shipment_city or '',
            'shipment_state': vendor.shipment_state or '',
            'shipment_pincode': vendor.shipment_pincode or '',
            'shipment_country': vendor.shipment_country or 'India',
            'shipment_latitude': float(vendor.shipment_latitude) if vendor.shipment_latitude else None,
            'shipment_longitude': float(vendor.shipment_longitude) if vendor.shipment_longitude else None,
        })
    
    elif request.method in ['PUT', 'PATCH']:
        # Update shipment address
        vendor.shipment_address = request.data.get('shipment_address', vendor.shipment_address)
        vendor.shipment_city = request.data.get('shipment_city', vendor.shipment_city)
        vendor.shipment_state = request.data.get('shipment_state', vendor.shipment_state)
        vendor.shipment_pincode = request.data.get('shipment_pincode', vendor.shipment_pincode)
        vendor.shipment_country = request.data.get('shipment_country', vendor.shipment_country or 'India')
        
        # Update coordinates if provided
        latitude = request.data.get('shipment_latitude')
        longitude = request.data.get('shipment_longitude')
        if latitude is not None:
            vendor.shipment_latitude = latitude
        if longitude is not None:
            vendor.shipment_longitude = longitude
        
        vendor.save()
        
        return Response({
            'success': True,
            'message': 'Shipment address updated successfully',
            'shipment_address': vendor.shipment_address or '',
            'shipment_city': vendor.shipment_city or '',
            'shipment_state': vendor.shipment_state or '',
            'shipment_pincode': vendor.shipment_pincode or '',
            'shipment_country': vendor.shipment_country or 'India',
            'shipment_latitude': float(vendor.shipment_latitude) if vendor.shipment_latitude else None,
            'shipment_longitude': float(vendor.shipment_longitude) if vendor.shipment_longitude else None,
        }, status=status.HTTP_200_OK)


# ==================== Seller Settings Views ====================
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsVendorUser])
def seller_settings(request):
    """Get or update seller profile and settings"""
    vendor = request.user.vendor_profile
    user = request.user
    
    if request.method == 'GET':
        return Response({
            'vendor': {
                'id': vendor.id,
                'business_name': vendor.business_name,
                'business_email': vendor.business_email,
                'business_phone': vendor.business_phone,
                'business_address': vendor.business_address,
                'city': vendor.city,
                'state': vendor.state,
                'pincode': vendor.pincode,
                'country': vendor.country,
                'gst_number': vendor.gst_number or '',
                'pan_number': vendor.pan_number or '',
                'business_type': vendor.business_type or '',
                'brand_name': vendor.brand_name,
                'status': vendor.status,
                'is_verified': vendor.is_verified,
                'low_stock_threshold': vendor.low_stock_threshold or 100,
                'account_holder_name': vendor.account_holder_name or '',
                'account_number': vendor.account_number or '',
                'ifsc_code': vendor.ifsc_code or '',
                'bank_name': vendor.bank_name or '',
                'branch_name': vendor.branch_name or '',
                'upi_id': vendor.upi_id or '',
                'shipment_address': vendor.shipment_address or '',
                'shipment_city': vendor.shipment_city or '',
                'shipment_state': vendor.shipment_state or '',
                'shipment_pincode': vendor.shipment_pincode or '',
                'shipment_country': vendor.shipment_country or 'India',
                'shipment_latitude': float(vendor.shipment_latitude) if vendor.shipment_latitude else None,
                'shipment_longitude': float(vendor.shipment_longitude) if vendor.shipment_longitude else None,
            },
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username or '',
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'mobile': user.mobile or '',
            }
        })
    
    elif request.method in ['PUT', 'PATCH']:
        # Update vendor profile
        vendor.business_name = request.data.get('business_name', vendor.business_name)
        vendor.business_email = request.data.get('business_email', vendor.business_email)
        vendor.business_phone = request.data.get('business_phone', vendor.business_phone)
        vendor.business_address = request.data.get('business_address', vendor.business_address)
        vendor.city = request.data.get('city', vendor.city)
        vendor.state = request.data.get('state', vendor.state)
        vendor.pincode = request.data.get('pincode', vendor.pincode)
        vendor.country = request.data.get('country', vendor.country)
        vendor.gst_number = request.data.get('gst_number', vendor.gst_number)
        vendor.pan_number = request.data.get('pan_number', vendor.pan_number)
        vendor.business_type = request.data.get('business_type', vendor.business_type)
        vendor.brand_name = request.data.get('brand_name', vendor.brand_name)
        
        # Update bank details
        vendor.account_holder_name = request.data.get('account_holder_name', vendor.account_holder_name)
        vendor.account_number = request.data.get('account_number', vendor.account_number)
        vendor.ifsc_code = request.data.get('ifsc_code', vendor.ifsc_code)
        vendor.bank_name = request.data.get('bank_name', vendor.bank_name)
        vendor.branch_name = request.data.get('branch_name', vendor.branch_name)
        vendor.upi_id = request.data.get('upi_id', vendor.upi_id)
        
        # Update shipment details
        vendor.shipment_address = request.data.get('shipment_address', vendor.shipment_address)
        vendor.shipment_city = request.data.get('shipment_city', vendor.shipment_city)
        vendor.shipment_state = request.data.get('shipment_state', vendor.shipment_state)
        vendor.shipment_pincode = request.data.get('shipment_pincode', vendor.shipment_pincode)
        vendor.shipment_country = request.data.get('shipment_country', vendor.shipment_country or 'India')
        
        # Update coordinates if provided
        latitude = request.data.get('shipment_latitude')
        longitude = request.data.get('shipment_longitude')
        if latitude is not None:
            vendor.shipment_latitude = latitude
        if longitude is not None:
            vendor.shipment_longitude = longitude
        
        # Update low stock threshold if provided
        low_stock_threshold = request.data.get('low_stock_threshold')
        if low_stock_threshold is not None:
            vendor.low_stock_threshold = int(low_stock_threshold)
        
        vendor.save()
        
        # Update user details
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.mobile = request.data.get('mobile', user.mobile)
        user.save()
        
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'vendor': {
                'id': vendor.id,
                'business_name': vendor.business_name,
                'business_email': vendor.business_email,
                'business_phone': vendor.business_phone,
                'business_address': vendor.business_address,
                'city': vendor.city,
                'state': vendor.state,
                'pincode': vendor.pincode,
                'country': vendor.country,
                'gst_number': vendor.gst_number or '',
                'pan_number': vendor.pan_number or '',
                'business_type': vendor.business_type or '',
                'brand_name': vendor.brand_name,
                'low_stock_threshold': vendor.low_stock_threshold or 100,
                'account_holder_name': vendor.account_holder_name or '',
                'account_number': vendor.account_number or '',
                'ifsc_code': vendor.ifsc_code or '',
                'bank_name': vendor.bank_name or '',
                'branch_name': vendor.branch_name or '',
                'upi_id': vendor.upi_id or '',
                'shipment_address': vendor.shipment_address or '',
                'shipment_city': vendor.shipment_city or '',
                'shipment_state': vendor.shipment_state or '',
                'shipment_pincode': vendor.shipment_pincode or '',
                'shipment_country': vendor.shipment_country or 'India',
                'shipment_latitude': float(vendor.shipment_latitude) if vendor.shipment_latitude else None,
                'shipment_longitude': float(vendor.shipment_longitude) if vendor.shipment_longitude else None,
            },
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username or '',
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'mobile': user.mobile or '',
            }
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsVendorUser])
def seller_change_password(request):
    """Change seller password"""
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not current_password or not new_password:
        return Response(
            {'error': 'Current password and new password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify current password
    if not user.check_password(current_password):
        return Response(
            {'error': 'Current password is incorrect'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate new password
    if len(new_password) < 8:
        return Response(
            {'error': 'New password must be at least 8 characters long'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response({
        'success': True,
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)

