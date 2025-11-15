from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q, Avg, F, DecimalField
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import os

from .permissions import IsAdminUser, IsAdminOrReadOnly
from .models import GlobalSettings, HomePageContent, BulkOrderPageContent
from .serializers import (
    DashboardStatsSerializer, AdminUserListSerializer, AdminUserDetailSerializer,
    AdminUserCreateSerializer, AdminUserUpdateSerializer, AdminCategorySerializer,
    AdminSubcategorySerializer, AdminColorSerializer, AdminMaterialSerializer,
    AdminProductListSerializer, AdminProductDetailSerializer,
    AdminOrderListSerializer, AdminOrderDetailSerializer, AdminDiscountSerializer,
    PaymentChargeSerializer, GlobalSettingsSerializer,
    AdminContactQuerySerializer, AdminBulkOrderSerializer, AdminLogSerializer,
    AdminCouponSerializer, HomePageContentSerializer, BulkOrderPageContentSerializer,
    AdminDataRequestSerializer, AdminBrandSerializer, AdminBrandDetailSerializer,
    SellerOrderListSerializer, AdminMediaSerializer, AdminPackagingFeedbackSerializer
)
from accounts.models import User, ContactQuery, BulkOrder, DataRequest, Vendor, Media, PackagingFeedback
from accounts.data_export_utils import export_orders_to_excel, export_addresses_to_excel, export_payment_options_to_excel
from products.models import (
    Category, Subcategory, Color, Material, Product, ProductImage,
    ProductVariant, ProductVariantImage, ProductSpecification, ProductFeature,
    ProductOffer, Discount, Coupon
)
from orders.models import Order, OrderItem, OrderStatusHistory, OrderNote
from .models import AdminLog
from .utils import create_admin_log
from .mixins import AdminLoggingMixin

User = get_user_model()


# ==================== Dashboard Views ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def dashboard_stats(request):
    """Get comprehensive dashboard statistics"""
    # Calculate date ranges
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # Basic stats
    total_users = User.objects.count()
    total_orders = Order.objects.count()
    
    # Total order value = sum of total_amount (including tax) that customers paid
    # This is the actual amount customers paid, not just the subtotal
    total_order_value = Order.objects.aggregate(
        total=Sum(F('total_amount'), output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total'] or Decimal('0.00')
    
    # Separate calculations for seller orders and Sixpine orders
    delivered_orders = Order.objects.filter(status='delivered')
    
    # Net profit from sellers = tax + platform fee from delivered orders (excluding Sixpine products)
    # Get orders that contain seller products (not Sixpine)
    seller_delivered_orders = delivered_orders.exclude(
        Q(items__product__brand__iexact='Sixpine') | Q(items__product__vendor__isnull=True)
    ).distinct()
    
    seller_net_profit = seller_delivered_orders.aggregate(
        total=Sum(F('tax_amount') + F('platform_fee'), output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total'] or Decimal('0.00')
    
    # Sixpine profit = total order value of Sixpine products (full amount for delivered orders)
    # Get orders that contain Sixpine products
    sixpine_delivered_orders = delivered_orders.filter(
        Q(items__product__brand__iexact='Sixpine') | Q(items__product__vendor__isnull=True)
    ).distinct()
    
    sixpine_profit = Decimal('0.00')
    for order in sixpine_delivered_orders:
        # Get Sixpine items in this order
        sixpine_items = order.items.filter(
            Q(product__brand__iexact='Sixpine') | Q(product__vendor__isnull=True)
        )
        if sixpine_items.exists():
            # Calculate Sixpine's share of total amount (proportional to their items)
            sixpine_items_subtotal = sixpine_items.aggregate(
                total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
            )['total'] or Decimal('0.00')
            
            if order.subtotal > 0:
                sixpine_share_ratio = sixpine_items_subtotal / order.subtotal
                sixpine_share_of_total = order.total_amount * sixpine_share_ratio
                sixpine_profit += sixpine_share_of_total
            else:
                sixpine_profit += sixpine_items_subtotal
    
    # Total net revenue = seller net profit + Sixpine profit
    total_net_revenue = seller_net_profit + sixpine_profit
    
    # Keep total_net_profit for backward compatibility (same as seller_net_profit)
    total_net_profit = seller_net_profit
    
    total_products = Product.objects.count()
    
    # Order summary stats
    orders_placed_count = Order.objects.count()
    delivered_orders_count = Order.objects.filter(status='delivered').count()
    cod_orders_count = Order.objects.filter(payment_method='COD').count()
    # Online payment = total orders - COD orders
    online_payment_orders_count = orders_placed_count - cod_orders_count
    
    # Low stock products - get global threshold, default to 100
    low_stock_threshold = GlobalSettings.get_setting('low_stock_threshold', 100)
    
    # Calculate low stock products: sum all variant stocks per product, compare to threshold
    products_with_stock = Product.objects.annotate(
        total_stock=Sum('variants__stock_quantity', filter=Q(variants__is_active=True))
    ).filter(total_stock__lt=low_stock_threshold, total_stock__isnull=False, is_active=True)
    low_stock_products = products_with_stock.count()
    
    # Recent orders (last 10)
    recent_orders = Order.objects.order_by('-created_at')[:10].values(
        'id', 'order_id', 'status', 'total_amount', 'created_at'
    )
    recent_orders = [{
        **order,
        'customer_name': Order.objects.get(id=order['id']).user.get_full_name() or Order.objects.get(id=order['id']).user.username
    } for order in recent_orders]
    
    # Top selling products with revenue calculation
    top_products = OrderItem.objects.values('product').annotate(
        sold=Sum('quantity'),
        revenue=Sum(F('quantity') * F('price'), output_field=DecimalField(max_digits=10, decimal_places=2))
    ).order_by('-sold')[:10]
    top_selling_products = []
    for item in top_products:
        product = Product.objects.get(id=item['product'])
        # Calculate revenue: sum of (quantity * price) for all order items of this product
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
        day_orders = Order.objects.filter(
            created_at__date=date,
            payment_status='paid'
        )
        revenue = day_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        orders_count = day_orders.count()
        sales_by_day.append({
            'date': date.isoformat(),
            'revenue': float(revenue),
            'orders': orders_count
        })
    
    data = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_order_value': str(total_order_value),
        'total_net_profit': str(total_net_profit),  # Seller net profit (tax + platform fee)
        'seller_net_profit': str(seller_net_profit),  # Explicit seller net profit
        'sixpine_profit': str(sixpine_profit),  # Sixpine product profit (full order value)
        'total_net_revenue': str(total_net_revenue),  # Total net revenue (seller + Sixpine)
        'total_products': total_products,
        'orders_placed_count': orders_placed_count,
        'delivered_orders_count': delivered_orders_count,
        'cod_orders_count': cod_orders_count,
        'online_payment_orders_count': online_payment_orders_count,
        'low_stock_products': low_stock_products,
        'recent_orders': list(recent_orders),
        'top_selling_products': top_selling_products,
        'sales_by_day': sales_by_day
    }
    
    serializer = DashboardStatsSerializer(data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def platform_analytics(request):
    """Get comprehensive platform analytics including seller profit, Sixpine products, and orders"""
    from decimal import Decimal
    from django.db.models import Count, Sum, F, Q, DecimalField
    from datetime import datetime, timedelta
    from accounts.models import Vendor
    
    # Calculate date ranges
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    twelve_months_ago = today - timedelta(days=365)
    
    # ========== ORDER STATS ==========
    total_orders = Order.objects.count()
    delivered_orders = Order.objects.filter(status='delivered')
    
    # Total order value (all orders)
    total_order_value = Order.objects.aggregate(
        total=Sum(F('total_amount'), output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total'] or Decimal('0.00')
    
    # Orders by status
    orders_by_status = Order.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Orders by month (last 12 months)
    orders_by_month = []
    for i in range(12):
        month_start = today.replace(day=1) - timedelta(days=30 * i)
        month_orders = Order.objects.filter(
            created_at__year=month_start.year,
            created_at__month=month_start.month
        )
        month_order_value = month_orders.aggregate(
            total=Sum(F('total_amount'), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'] or Decimal('0.00')
        
        orders_by_month.append({
            'month': f"{month_start.year}-{str(month_start.month).zfill(2)}",
            'count': month_orders.count(),
            'order_value': float(month_order_value)
        })
    orders_by_month.reverse()
    
    # Payment methods
    payment_methods = Order.objects.values('payment_method').annotate(
        count=Count('id'),
        total_value=Sum(F('total_amount'), output_field=DecimalField(max_digits=10, decimal_places=2))
    ).order_by('-count')
    
    # ========== SELLER PROFIT STATS ==========
    # Get orders with seller products (not Sixpine)
    seller_orders = Order.objects.filter(
        items__product__vendor__isnull=False
    ).exclude(
        Q(items__product__brand__iexact='Sixpine')
    ).distinct()
    
    seller_delivered_orders = seller_orders.filter(status='delivered')
    
    # Seller net profit = tax + platform fee from delivered orders
    seller_net_profit = seller_delivered_orders.aggregate(
        total=Sum(F('tax_amount') + F('platform_fee'), output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total'] or Decimal('0.00')
    
    # Seller order value (proportional share of total_amount)
    seller_order_value = Decimal('0.00')
    for order in seller_orders:
        seller_items = order.items.filter(product__vendor__isnull=False).exclude(
            Q(product__brand__iexact='Sixpine')
        )
        if seller_items.exists():
            seller_items_subtotal = seller_items.aggregate(
                total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
            )['total'] or Decimal('0.00')
            
            if order.subtotal > 0:
                seller_share_ratio = seller_items_subtotal / order.subtotal
                seller_share_of_total = order.total_amount * seller_share_ratio
                seller_order_value += seller_share_of_total
            else:
                seller_order_value += seller_items_subtotal
    
    # Seller orders by month
    seller_orders_by_month = []
    for i in range(12):
        month_start = today.replace(day=1) - timedelta(days=30 * i)
        month_seller_orders = seller_orders.filter(
            created_at__year=month_start.year,
            created_at__month=month_start.month
        )
        
        month_seller_value = Decimal('0.00')
        for order in month_seller_orders:
            seller_items = order.items.filter(product__vendor__isnull=False).exclude(
                Q(product__brand__iexact='Sixpine')
            )
            if seller_items.exists():
                seller_items_subtotal = seller_items.aggregate(
                    total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
                )['total'] or Decimal('0.00')
                
                if order.subtotal > 0:
                    seller_share_ratio = seller_items_subtotal / order.subtotal
                    seller_share_of_total = order.total_amount * seller_share_ratio
                    month_seller_value += seller_share_of_total
                else:
                    month_seller_value += seller_items_subtotal
        
        seller_orders_by_month.append({
            'month': f"{month_start.year}-{str(month_start.month).zfill(2)}",
            'count': month_seller_orders.count(),
            'order_value': float(month_seller_value),
            'net_profit': float(seller_delivered_orders.filter(
                created_at__year=month_start.year,
                created_at__month=month_start.month
            ).aggregate(
                total=Sum(F('tax_amount') + F('platform_fee'), output_field=DecimalField(max_digits=10, decimal_places=2))
            )['total'] or Decimal('0.00'))
        })
    seller_orders_by_month.reverse()
    
    # ========== SIXPINE PRODUCTS STATS ==========
    # Get Sixpine products (brand='Sixpine' or vendor is null)
    sixpine_products = Product.objects.filter(
        Q(brand__iexact='Sixpine') | Q(vendor__isnull=True)
    )
    total_sixpine_products = sixpine_products.count()
    active_sixpine_products = sixpine_products.filter(is_active=True).count()
    
    # Get orders with Sixpine products
    sixpine_orders = Order.objects.filter(
        Q(items__product__brand__iexact='Sixpine') | Q(items__product__vendor__isnull=True)
    ).distinct()
    
    sixpine_delivered_orders = sixpine_orders.filter(status='delivered')
    
    # Sixpine profit = total order value of Sixpine products (full amount for delivered orders)
    sixpine_profit = Decimal('0.00')
    for order in sixpine_delivered_orders:
        sixpine_items = order.items.filter(
            Q(product__brand__iexact='Sixpine') | Q(product__vendor__isnull=True)
        )
        if sixpine_items.exists():
            sixpine_items_subtotal = sixpine_items.aggregate(
                total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
            )['total'] or Decimal('0.00')
            
            if order.subtotal > 0:
                sixpine_share_ratio = sixpine_items_subtotal / order.subtotal
                sixpine_share_of_total = order.total_amount * sixpine_share_ratio
                sixpine_profit += sixpine_share_of_total
            else:
                sixpine_profit += sixpine_items_subtotal
    
    # Sixpine order value (all orders, not just delivered)
    sixpine_order_value = Decimal('0.00')
    for order in sixpine_orders:
        sixpine_items = order.items.filter(
            Q(product__brand__iexact='Sixpine') | Q(product__vendor__isnull=True)
        )
        if sixpine_items.exists():
            sixpine_items_subtotal = sixpine_items.aggregate(
                total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
            )['total'] or Decimal('0.00')
            
            if order.subtotal > 0:
                sixpine_share_ratio = sixpine_items_subtotal / order.subtotal
                sixpine_share_of_total = order.total_amount * sixpine_share_ratio
                sixpine_order_value += sixpine_share_of_total
            else:
                sixpine_order_value += sixpine_items_subtotal
    
    # Sixpine orders by month
    sixpine_orders_by_month = []
    for i in range(12):
        month_start = today.replace(day=1) - timedelta(days=30 * i)
        month_sixpine_orders = sixpine_orders.filter(
            created_at__year=month_start.year,
            created_at__month=month_start.month
        )
        
        month_sixpine_value = Decimal('0.00')
        for order in month_sixpine_orders:
            sixpine_items = order.items.filter(
                Q(product__brand__iexact='Sixpine') | Q(product__vendor__isnull=True)
            )
            if sixpine_items.exists():
                sixpine_items_subtotal = sixpine_items.aggregate(
                    total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
                )['total'] or Decimal('0.00')
                
                if order.subtotal > 0:
                    sixpine_share_ratio = sixpine_items_subtotal / order.subtotal
                    sixpine_share_of_total = order.total_amount * sixpine_share_ratio
                    month_sixpine_value += sixpine_share_of_total
                else:
                    month_sixpine_value += sixpine_items_subtotal
        
        # Calculate Sixpine profit for this month (from delivered orders)
        month_sixpine_profit = Decimal('0.00')
        month_delivered_sixpine_orders = sixpine_delivered_orders.filter(
            created_at__year=month_start.year,
            created_at__month=month_start.month
        )
        for order in month_delivered_sixpine_orders:
            sixpine_items = order.items.filter(
                Q(product__brand__iexact='Sixpine') | Q(product__vendor__isnull=True)
            )
            if sixpine_items.exists():
                sixpine_items_subtotal = sixpine_items.aggregate(
                    total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
                )['total'] or Decimal('0.00')
                
                if order.subtotal > 0:
                    sixpine_share_ratio = sixpine_items_subtotal / order.subtotal
                    sixpine_share_of_total = order.total_amount * sixpine_share_ratio
                    month_sixpine_profit += sixpine_share_of_total
                else:
                    month_sixpine_profit += sixpine_items_subtotal
        
        sixpine_orders_by_month.append({
            'month': f"{month_start.year}-{str(month_start.month).zfill(2)}",
            'count': month_sixpine_orders.count(),
            'order_value': float(month_sixpine_value),
            'profit': float(month_sixpine_profit)
        })
    sixpine_orders_by_month.reverse()
    
    # Top selling Sixpine products
    sixpine_top_products = OrderItem.objects.filter(
        Q(product__brand__iexact='Sixpine') | Q(product__vendor__isnull=True)
    ).values('product').annotate(
        sold=Sum('quantity'),
        revenue=Sum(F('quantity') * F('price'), output_field=DecimalField(max_digits=10, decimal_places=2))
    ).order_by('-sold')[:10]
    
    top_sixpine_products = []
    for item in sixpine_top_products:
        try:
            product = Product.objects.get(id=item['product'])
            top_sixpine_products.append({
                'id': product.id,
                'title': product.title,
                'sold': item['sold'],
                'revenue': float(item.get('revenue') or Decimal('0.00'))
            })
        except Product.DoesNotExist:
            continue
    
    # ========== PLATFORM SUMMARY ==========
    total_net_revenue = seller_net_profit + sixpine_profit
    total_products = Product.objects.count()
    total_seller_products = Product.objects.filter(vendor__isnull=False).exclude(
        Q(brand__iexact='Sixpine')
    ).count()
    
    # Total vendors
    total_vendors = Vendor.objects.filter(status='active').count()
    
    data = {
        'order_stats': {
            'total_orders': total_orders,
            'total_order_value': float(total_order_value),
            'average_order_value': float(total_order_value / total_orders) if total_orders > 0 else 0,
            'orders_by_status': [
                {'status': item['status'], 'count': item['count']}
                for item in orders_by_status
            ],
            'orders_by_month': orders_by_month,
            'payment_methods': [
                {
                    'method': item['payment_method'] or 'Unknown',
                    'count': item['count'],
                    'total_value': float(item.get('total_value') or Decimal('0.00'))
                }
                for item in payment_methods
            ]
        },
        'seller_stats': {
            'total_vendors': total_vendors,
            'total_seller_products': total_seller_products,
            'total_seller_orders': seller_orders.count(),
            'seller_order_value': float(seller_order_value),
            'seller_net_profit': float(seller_net_profit),
            'orders_by_month': seller_orders_by_month
        },
        'sixpine_stats': {
            'total_products': total_sixpine_products,
            'active_products': active_sixpine_products,
            'total_orders': sixpine_orders.count(),
            'sixpine_order_value': float(sixpine_order_value),
            'sixpine_profit': float(sixpine_profit),
            'orders_by_month': sixpine_orders_by_month,
            'top_products': top_sixpine_products
        },
        'platform_summary': {
            'total_products': total_products,
            'total_order_value': float(total_order_value),
            'total_net_revenue': float(total_net_revenue),
            'seller_net_profit': float(seller_net_profit),
            'sixpine_profit': float(sixpine_profit)
        }
    }
    
    return Response(data)


# ==================== User Management Views ====================
class AdminUserViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for user management"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserListSerializer
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminUserDetailSerializer
        elif self.action == 'create':
            return AdminUserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AdminUserUpdateSerializer
        return AdminUserListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        is_active = self.request.query_params.get('is_active', None)
        is_staff = self.request.query_params.get('is_staff', None)
        
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(mobile__icontains=search)
            )
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if is_staff is not None:
            queryset = queryset.filter(is_staff=is_staff.lower() == 'true')
        
        return queryset
    
    def perform_destroy(self, instance):
        """Override destroy to check for orders and handle ProtectedError"""
        from django.db.models.deletion import ProtectedError
        from rest_framework.exceptions import ValidationError, PermissionDenied
        
        # Check if user is superuser
        if instance.is_superuser:
            raise PermissionDenied("Cannot delete superuser accounts")
        
        # Check if user has orders
        order_count = Order.objects.filter(user=instance).count()
        if order_count > 0:
            raise ValidationError(
                f"Cannot delete user because they have {order_count} order(s). "
                "Please delete or reassign the orders first."
            )
        
        # Try to delete and catch ProtectedError
        try:
            # Log before deletion
            try:
                create_admin_log(
                    request=self.request,
                    action_type='delete',
                    model_name='User',
                    object_id=instance.id,
                    object_repr=str(instance),
                    details={'action': 'delete'}
                )
            except Exception as e:
                print(f"Error creating admin log: {e}")
            
            instance.delete()
        except ProtectedError as e:
            # Extract order information from the error
            protected_objects = list(e.protected_objects)
            order_count = len([obj for obj in protected_objects if isinstance(obj, Order)])
            
            if order_count > 0:
                raise ValidationError(
                    f"Cannot delete user because they have {order_count} order(s). "
                    "Please delete or reassign the orders first."
                )
            else:
                raise ValidationError(
                    "Cannot delete user because they are referenced by other records. "
                    "Please remove all associated data first."
                )
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle user active status"""
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        
        create_admin_log(
            request=request,
            action_type='activate' if user.is_active else 'deactivate',
            model_name='User',
            object_id=user.id,
            object_repr=str(user)
        )
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_staff(self, request, pk=None):
        """Toggle user staff status"""
        user = self.get_object()
        user.is_staff = not user.is_staff
        user.save()
        
        create_admin_log(
            request=request,
            action_type='update',
            model_name='User',
            object_id=user.id,
            object_repr=str(user),
            details={'is_staff': user.is_staff}
        )
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset user password"""
        user = self.get_object()
        password = request.data.get('password')
        
        if not password:
            return Response(
                {'error': 'Password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(password)
        user.save()
        
        create_admin_log(
            request=request,
            action_type='update',
            model_name='User',
            object_id=user.id,
            object_repr=str(user),
            details={'action': 'password_reset'}
        )
        
        return Response({'message': 'Password reset successfully'})


# ==================== Category Management Views ====================
class AdminCategoryViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for category management"""
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    queryset = Category.objects.all().order_by('sort_order', 'name')
    serializer_class = AdminCategorySerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def hierarchical(self, request):
        """Get categories with subcategories"""
        categories = Category.objects.filter(is_active=True).prefetch_related('subcategories')
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


# ==================== Subcategory Management Views ====================
class AdminSubcategoryViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for subcategory management"""
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    queryset = Subcategory.objects.all().order_by('sort_order', 'name')
    serializer_class = AdminSubcategorySerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category', None)
        search = self.request.query_params.get('search', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if category:
            queryset = queryset.filter(category_id=category)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


# ==================== Color Management Views ====================
class AdminColorViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for color management"""
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    queryset = Color.objects.all().order_by('name')
    serializer_class = AdminColorSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset


# ==================== Material Management Views ====================
class AdminMaterialViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for material management"""
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    queryset = Material.objects.all().order_by('name')
    serializer_class = AdminMaterialSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset


# ==================== Product Management Views ====================
class AdminProductViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for product management"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Product.objects.all().select_related('category', 'subcategory').prefetch_related(
        'images', 'variants', 'specifications', 'features'
    ).order_by('-created_at')
    serializer_class = AdminProductListSerializer
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return AdminProductDetailSerializer
        return AdminProductListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)
        subcategory = self.request.query_params.get('subcategory', None)
        is_active = self.request.query_params.get('is_active', None)
        is_featured = self.request.query_params.get('is_featured', None)
        vendor = self.request.query_params.get('vendor', None)
        brand = self.request.query_params.get('brand', None)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(sku__icontains=search) |
                Q(short_description__icontains=search) |
                Q(long_description__icontains=search) |
                Q(brand__icontains=search)
            )
        if category:
            queryset = queryset.filter(category_id=category)
        if subcategory:
            queryset = queryset.filter(subcategory_id=subcategory)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured.lower() == 'true')
        if vendor:
            queryset = queryset.filter(vendor_id=vendor)
        if brand:
            queryset = queryset.filter(brand__iexact=brand)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle product active status"""
        product = self.get_object()
        product.is_active = not product.is_active
        product.save()
        
        create_admin_log(
            request=request,
            action_type='activate' if product.is_active else 'deactivate',
            model_name='Product',
            object_id=product.id,
            object_repr=str(product)
        )
        
        serializer = self.get_serializer(product)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_featured(self, request, pk=None):
        """Toggle product featured status"""
        product = self.get_object()
        product.is_featured = not product.is_featured
        product.save()
        
        create_admin_log(
            request=request,
            action_type='update',
            model_name='Product',
            object_id=product.id,
            object_repr=str(product),
            details={'is_featured': product.is_featured}
        )
        
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
            variant = product.variants.get(id=variant_id)
            variant.stock_quantity = quantity
            variant.save()
            
            create_admin_log(
                request=request,
                action_type='update',
                model_name='ProductVariant',
                object_id=variant.id,
                object_repr=str(variant),
                details={'stock_quantity': quantity}
            )
            
            return Response({
                'message': 'Stock updated successfully',
                'variant_id': variant.id,
                'stock_quantity': variant.stock_quantity
            })
        except ProductVariant.DoesNotExist:
            return Response(
                {'error': 'Variant not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ==================== Order Management Views ====================
class AdminOrderViewSet(AdminLoggingMixin, viewsets.ReadOnlyModelViewSet):
    """Admin viewset for order management (read-only with custom actions)"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Order.objects.all().select_related('user').prefetch_related(
        'items', 'status_history', 'notes'
    ).order_by('-created_at')
    serializer_class = AdminOrderListSerializer
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminOrderDetailSerializer
        return AdminOrderListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        status_filter = self.request.query_params.get('status', None)
        payment_status = self.request.query_params.get('payment_status', None)
        vendor = self.request.query_params.get('vendor', None)
        exclude_sixpine = self.request.query_params.get('exclude_sixpine', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__mobile__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        if vendor:
            # If vendor is "sixpine", filter by brand="Sixpine" or vendor is None
            if vendor == 'sixpine':
                queryset = queryset.filter(
                    Q(items__product__brand__iexact='Sixpine') | Q(items__product__vendor__isnull=True)
                ).distinct()
            else:
                queryset = queryset.filter(items__vendor_id=vendor).distinct()
        elif exclude_sixpine == 'true':
            # Exclude Sixpine orders (orders with brand="Sixpine" or no vendor)
            queryset = queryset.exclude(
                Q(items__product__brand__iexact='Sixpine') | Q(items__product__vendor__isnull=True)
            ).distinct()
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = order.status
        order.status = new_status
        order.save()
        
        # Create status history entry
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            notes=notes,
            changed_by=request.user
        )
        
        create_admin_log(
            request=request,
            action_type='update',
            model_name='Order',
            object_id=order.id,
            object_repr=str(order),
            details={'status': {'old': old_status, 'new': new_status}}
        )
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_payment_status(self, request, pk=None):
        """Update order payment status"""
        order = self.get_object()
        new_payment_status = request.data.get('payment_status')
        notes = request.data.get('notes', '')
        
        if not new_payment_status:
            return Response(
                {'error': 'Payment status is required'},
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
        
        create_admin_log(
            request=request,
            action_type='update',
            model_name='Order',
            object_id=order.id,
            object_repr=str(order),
            details={'payment_status': {'old': old_payment_status, 'new': new_payment_status}}
        )
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_tracking(self, request, pk=None):
        """Update order tracking information"""
        order = self.get_object()
        tracking_number = request.data.get('tracking_number')
        estimated_delivery = request.data.get('estimated_delivery')
        notes = request.data.get('notes', '')
        
        if tracking_number:
            order.tracking_number = tracking_number
        if estimated_delivery:
            order.estimated_delivery = estimated_delivery
        order.save()
        
        # Create order note if provided
        if notes:
            OrderNote.objects.create(
                order=order,
                note=notes,
                created_by=request.user
            )
        
        create_admin_log(
            request=request,
            action_type='update',
            model_name='Order',
            object_id=order.id,
            object_repr=str(order),
            details={'tracking_number': tracking_number, 'estimated_delivery': estimated_delivery}
        )
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def notes(self, request, pk=None):
        """Get order notes"""
        order = self.get_object()
        notes = order.notes.all().order_by('-created_at')
        notes_data = [{
            'id': note.id,
            'note': note.note,
            'created_by': note.created_by.username if note.created_by else 'System',
            'created_at': note.created_at
        } for note in notes]
        return Response(notes_data)
    
    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """Add note to order"""
        order = self.get_object()
        note_text = request.data.get('note')
        
        if not note_text:
            return Response(
                {'error': 'Note text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        note = OrderNote.objects.create(
            order=order,
            note=note_text,
            created_by=request.user
        )
        
        create_admin_log(
            request=request,
            action_type='update',
            model_name='Order',
            object_id=order.id,
            object_repr=str(order),
            details={'action': 'note_added', 'note_id': note.id}
        )
        
        return Response({
            'id': note.id,
            'note': note.note,
            'created_by': note.created_by.username,
            'created_at': note.created_at
        })


# ==================== Discount Management Views ====================
class AdminDiscountViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for discount management"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Discount.objects.all().order_by('-created_at')
    serializer_class = AdminDiscountSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


# ==================== Coupon Management Views ====================
class AdminCouponViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for coupon management"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Coupon.objects.all().order_by('-created_at')
    serializer_class = AdminCouponSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
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


# ==================== Payment Charges Settings ====================
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated, IsAdminUser])
def payment_charges_settings(request):
    """Get or update payment charges settings"""
    def get_setting_value(key, default):
        value = GlobalSettings.get_setting(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        return value
    
    if request.method == 'GET':
        settings = {
            'platform_fee_upi': str(GlobalSettings.get_setting('platform_fee_upi', '0.00')),
            'platform_fee_card': str(GlobalSettings.get_setting('platform_fee_card', '2.36')),
            'platform_fee_netbanking': str(GlobalSettings.get_setting('platform_fee_netbanking', '2.36')),
            'platform_fee_cod': str(GlobalSettings.get_setting('platform_fee_cod', '0.00')),
            'tax_rate': str(GlobalSettings.get_setting('tax_rate', '5.00')),
            'razorpay_enabled': get_setting_value('razorpay_enabled', True),
            'cod_enabled': get_setting_value('cod_enabled', True),
        }
        serializer = PaymentChargeSerializer(settings)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        data = request.data
        
        # Update platform fees
        if 'platform_fee_upi' in data:
            GlobalSettings.set_setting('platform_fee_upi', data.get('platform_fee_upi', '0.00'), 'Platform fee percentage for UPI payments')
        if 'platform_fee_card' in data:
            GlobalSettings.set_setting('platform_fee_card', data.get('platform_fee_card', '2.36'), 'Platform fee percentage for Credit/Debit Card payments')
        if 'platform_fee_netbanking' in data:
            GlobalSettings.set_setting('platform_fee_netbanking', data.get('platform_fee_netbanking', '2.36'), 'Platform fee percentage for Net Banking payments')
        if 'platform_fee_cod' in data:
            GlobalSettings.set_setting('platform_fee_cod', data.get('platform_fee_cod', '0.00'), 'Platform fee percentage for COD payments')
        
        # Update tax rate
        if 'tax_rate' in data:
            GlobalSettings.set_setting('tax_rate', data.get('tax_rate', '5.00'), 'Tax rate percentage')
        
        # Update payment method enabled flags
        if 'razorpay_enabled' in data:
            GlobalSettings.set_setting('razorpay_enabled', data.get('razorpay_enabled', True), 'Enable Razorpay payment gateway')
        if 'cod_enabled' in data:
            GlobalSettings.set_setting('cod_enabled', data.get('cod_enabled', True), 'Enable Cash on Delivery')
        
        create_admin_log(
            request=request,
            action_type='update',
            model_name='GlobalSettings',
            object_id=None,
            object_repr='Payment Charges',
            details=data
        )
        
        # Return updated settings
        settings = {
            'platform_fee_upi': str(GlobalSettings.get_setting('platform_fee_upi', '0.00')),
            'platform_fee_card': str(GlobalSettings.get_setting('platform_fee_card', '2.36')),
            'platform_fee_netbanking': str(GlobalSettings.get_setting('platform_fee_netbanking', '2.36')),
            'platform_fee_cod': str(GlobalSettings.get_setting('platform_fee_cod', '0.00')),
            'tax_rate': str(GlobalSettings.get_setting('tax_rate', '5.00')),
            'razorpay_enabled': get_setting_value('razorpay_enabled', True),
            'cod_enabled': get_setting_value('cod_enabled', True),
        }
        serializer = PaymentChargeSerializer(settings)
        return Response(serializer.data)


# ==================== Global Settings ====================
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated, IsAdminUser])
def global_settings(request):
    """Get or update global settings"""
    key = request.query_params.get('key', None)
    
    if request.method == 'GET':
        if key:
            try:
                setting = GlobalSettings.objects.get(key=key)
                serializer = GlobalSettingsSerializer(setting)
                return Response(serializer.data)
            except GlobalSettings.DoesNotExist:
                return Response(
                    {'error': 'Setting not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            settings = GlobalSettings.objects.all()
            serializer = GlobalSettingsSerializer(settings, many=True)
            return Response(serializer.data)
    
    elif request.method == 'PUT':
        data = request.data
        key = data.get('key')
        value = data.get('value')
        description = data.get('description', '')
        
        if not key:
            return Response(
                {'error': 'key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Allow empty strings for optional fields (like social media URLs)
        if value is None:
            return Response(
                {'error': 'value is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        setting = GlobalSettings.set_setting(key, str(value), description)
        
        create_admin_log(
            request=request,
            action_type='update',
            model_name='GlobalSettings',
            object_id=setting.id,
            object_repr=str(setting),
            details={'key': key, 'value': value}
        )
        
        serializer = GlobalSettingsSerializer(setting)
        return Response(serializer.data)


# ==================== Contact Query Views ====================
class AdminContactQueryViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for contact query management"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = ContactQuery.objects.all().order_by('-created_at')
    serializer_class = AdminContactQuerySerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        status_filter = self.request.query_params.get('status', None)
        
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(message__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update contact query status"""
        contact_query = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        contact_query.status = new_status
        if notes:
            contact_query.admin_notes = notes
        contact_query.save()
        
        serializer = self.get_serializer(contact_query)
        return Response(serializer.data)


# ==================== Bulk Order Views ====================
class AdminBulkOrderViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for bulk order management"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = BulkOrder.objects.all().select_related('assigned_to').order_by('-created_at')
    serializer_class = AdminBulkOrderSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        status_filter = self.request.query_params.get('status', None)
        assigned_to = self.request.query_params.get('assigned_to', None)
        
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_number__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update bulk order status"""
        bulk_order = self.get_object()
        status_value = request.data.get('status')
        notes = request.data.get('notes', '')
        quoted_price = request.data.get('quoted_price', None)
        
        if status_value not in dict(BulkOrder.STATUS_CHOICES).keys():
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bulk_order.status = status_value
        if notes:
            bulk_order.admin_notes = notes
        if quoted_price is not None:
            bulk_order.quoted_price = quoted_price
        bulk_order.save()
        
        serializer = self.get_serializer(bulk_order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign bulk order to admin user"""
        bulk_order = self.get_object()
        admin_id = request.data.get('admin_id')
        
        try:
            admin_user = User.objects.get(id=admin_id, is_staff=True)
            bulk_order.assigned_to = admin_user
            bulk_order.save()
            
            serializer = self.get_serializer(bulk_order)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Admin user not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ==================== Admin Log Views ====================
class AdminLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin viewset for viewing logs (read-only)"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = AdminLog.objects.all().order_by('-created_at')
    serializer_class = AdminLogSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        action_type = self.request.query_params.get('action_type', None)
        model_name = self.request.query_params.get('model_name', None)
        user_id = self.request.query_params.get('user', None)
        search = self.request.query_params.get('search', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        if model_name:
            queryset = queryset.filter(model_name=model_name)
        if user_id:
            # Validate that user_id is a valid integer
            try:
                user_id_int = int(user_id)
                queryset = queryset.filter(user_id=user_id_int)
            except (ValueError, TypeError):
                # If not a valid integer, ignore the filter
                pass
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search) |
                Q(user__username__icontains=search) |
                Q(model_name__icontains=search) |
                Q(object_repr__icontains=search) |
                Q(action_type__icontains=search)
            )
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Override list to provide pagination"""
        from rest_framework.response import Response
        from rest_framework.pagination import PageNumberPagination
        
        class AdminLogPagination(PageNumberPagination):
            page_size = 20
            page_size_query_param = 'page_size'
            max_page_size = 100
        
        queryset = self.filter_queryset(self.get_queryset())
        paginator = AdminLogPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ==================== Home Page Content Views ====================
class AdminHomePageContentViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for managing home page content sections"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = HomePageContent.objects.all()
    serializer_class = HomePageContentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        section_key = self.request.query_params.get('section_key', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if section_key:
            queryset = queryset.filter(section_key=section_key)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('order', 'section_name')
    
    def perform_create(self, serializer):
        """Create with logging"""
        instance = serializer.save()
        create_admin_log(
            request=self.request,
            action_type='create',
            model_name='HomePageContent',
            object_id=instance.id,
            object_repr=str(instance),
            details={'section_key': instance.section_key}
        )
    
    def perform_update(self, serializer):
        """Update with logging"""
        instance = serializer.save()
        create_admin_log(
            request=self.request,
            action_type='update',
            model_name='HomePageContent',
            object_id=instance.id,
            object_repr=str(instance),
            details={'section_key': instance.section_key}
        )
    
    def perform_destroy(self, instance):
        """Delete with logging"""
        create_admin_log(
            request=self.request,
            action_type='delete',
            model_name='HomePageContent',
            object_id=instance.id,
            object_repr=str(instance),
            details={'section_key': instance.section_key}
        )
        instance.delete()


# ==================== Bulk Order Page Content Views ====================
class AdminBulkOrderPageContentViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for managing bulk order page content sections"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = BulkOrderPageContent.objects.all()
    serializer_class = BulkOrderPageContentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        section_key = self.request.query_params.get('section_key', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if section_key:
            queryset = queryset.filter(section_key=section_key)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('order', 'section_name')
    
    def perform_create(self, serializer):
        """Create with logging"""
        instance = serializer.save()
        create_admin_log(
            request=self.request,
            action_type='create',
            model_name='BulkOrderPageContent',
            object_id=instance.id,
            object_repr=str(instance),
            details={'section_key': instance.section_key}
        )
    
    def perform_update(self, serializer):
        """Update with logging"""
        instance = serializer.save()
        create_admin_log(
            request=self.request,
            action_type='update',
            model_name='BulkOrderPageContent',
            object_id=instance.id,
            object_repr=str(instance),
            details={'section_key': instance.section_key}
        )
    
    def perform_destroy(self, instance):
        """Delete with logging"""
        create_admin_log(
            request=self.request,
            action_type='delete',
            model_name='BulkOrderPageContent',
            object_id=instance.id,
            object_repr=str(instance),
            details={'section_key': instance.section_key}
        )
        instance.delete()


class AdminDataRequestViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """ViewSet for managing data requests"""
    queryset = DataRequest.objects.all().order_by('-requested_at')
    serializer_class = AdminDataRequestSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by status if provided
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        # Filter by request_type if provided
        request_type = self.request.query_params.get('request_type', None)
        if request_type:
            queryset = queryset.filter(request_type=request_type)
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a data request and generate Excel file"""
        data_request = self.get_object()
        
        if data_request.status != 'pending':
            return Response({
                'error': f'Request is already {data_request.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            import os
            from django.conf import settings
            
            # Generate file path
            file_name = f"{data_request.user.email}_{data_request.request_type}_{data_request.id}.xlsx"
            media_root = getattr(settings, 'MEDIA_ROOT', 'media')
            data_export_dir = os.path.join(media_root, 'data_exports')
            file_path = os.path.join(data_export_dir, file_name)
            
            # Generate Excel file based on request type
            if data_request.request_type == 'orders':
                export_orders_to_excel(data_request.user, file_path)
            elif data_request.request_type == 'addresses':
                export_addresses_to_excel(data_request.user, file_path)
            elif data_request.request_type == 'payment_options':
                export_payment_options_to_excel(data_request.user, file_path)
            
            # Update request status
            data_request.status = 'approved'
            data_request.approved_at = timezone.now()
            data_request.approved_by = request.user
            data_request.file_path = file_path
            data_request.save()
            
            # Log action
            create_admin_log(
                request=request,
                action_type='update',
                model_name='DataRequest',
                object_id=data_request.id,
                object_repr=str(data_request),
                details={'action': 'approve', 'request_type': data_request.request_type}
            )
            
            return Response({
                'success': True,
                'message': 'Request approved and file generated successfully',
                'data': AdminDataRequestSerializer(data_request).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to approve request: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a data request"""
        data_request = self.get_object()
        
        if data_request.status != 'pending':
            return Response({
                'error': f'Request is already {data_request.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        admin_notes = request.data.get('admin_notes', '')
        
        data_request.status = 'rejected'
        data_request.approved_by = request.user
        data_request.admin_notes = admin_notes
        data_request.save()
        
        # Log action
        create_admin_log(
            request=request,
            action_type='update',
            model_name='DataRequest',
            object_id=data_request.id,
            object_repr=str(data_request),
            details={'action': 'reject'}
        )
        
        return Response({
            'success': True,
            'message': 'Request rejected successfully',
            'data': AdminDataRequestSerializer(data_request).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download the generated Excel file"""
        data_request = self.get_object()
        
        if data_request.status != 'approved' and data_request.status != 'completed':
            return Response({
                'error': 'Request is not approved yet'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not data_request.file_path or not os.path.exists(data_request.file_path):
            return Response({
                'error': 'File not found. Please regenerate the file.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        from django.http import FileResponse
        
        file_name = os.path.basename(data_request.file_path)
        response = FileResponse(open(data_request.file_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        
        # Mark as completed
        if data_request.status == 'approved':
            data_request.status = 'completed'
            data_request.completed_at = timezone.now()
            data_request.save()
        
        return response
    
    def perform_destroy(self, instance):
        """Override destroy to delete file and log action"""
        # Delete the Excel file if it exists
        if instance.file_path and os.path.exists(instance.file_path):
            try:
                os.remove(instance.file_path)
            except Exception as e:
                print(f"Error deleting file {instance.file_path}: {e}")
        
        # Log the deletion
        create_admin_log(
            request=self.request,
            action_type='delete',
            model_name='DataRequest',
            object_id=instance.id,
            object_repr=str(instance),
            details={'action': 'delete', 'request_type': instance.request_type, 'user_email': instance.user.email}
        )
        
        instance.delete()
    
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Delete multiple data requests"""
        request_ids = request.data.get('ids', [])
        
        if not request_ids or not isinstance(request_ids, list):
            return Response({
                'error': 'Please provide a list of request IDs to delete'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = 0
        errors = []
        
        for request_id in request_ids:
            try:
                data_request = DataRequest.objects.get(id=request_id)
                
                # Delete the Excel file if it exists
                if data_request.file_path and os.path.exists(data_request.file_path):
                    try:
                        os.remove(data_request.file_path)
                    except Exception as e:
                        print(f"Error deleting file {data_request.file_path}: {e}")
                
                # Log the deletion
                create_admin_log(
                    request=request,
                    action_type='delete',
                    model_name='DataRequest',
                    object_id=data_request.id,
                    object_repr=str(data_request),
                    details={'action': 'bulk_delete', 'request_type': data_request.request_type, 'user_email': data_request.user.email}
                )
                
                data_request.delete()
                deleted_count += 1
            except DataRequest.DoesNotExist:
                errors.append(f"Request {request_id} not found")
            except Exception as e:
                errors.append(f"Error deleting request {request_id}: {str(e)}")
        
        response_data = {
            'success': True,
            'message': f'Successfully deleted {deleted_count} request(s)',
            'deleted_count': deleted_count
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(response_data, status=status.HTTP_200_OK)


# ==================== Brand/Vendor Management Views ====================
class AdminBrandViewSet(AdminLoggingMixin, viewsets.ReadOnlyModelViewSet):
    """Admin viewset for brand/vendor management"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Vendor.objects.all().select_related('user').order_by('-created_at')
    serializer_class = AdminBrandSerializer
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminBrandDetailSerializer
        return AdminBrandSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        status_filter = self.request.query_params.get('status', None)
        is_verified = self.request.query_params.get('is_verified', None)
        
        if search:
            queryset = queryset.filter(
                Q(business_name__icontains=search) |
                Q(brand_name__icontains=search) |
                Q(business_email__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend a brand/vendor"""
        vendor = self.get_object()
        vendor.status = 'suspended'
        vendor.save()
        
        create_admin_log(
            request=request,
            action_type='update',
            model_name='Vendor',
            object_id=vendor.id,
            object_repr=str(vendor),
            details={'status': 'suspended'}
        )
        
        serializer = self.get_serializer(vendor)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a brand/vendor"""
        vendor = self.get_object()
        vendor.status = 'active'
        vendor.is_verified = True
        vendor.save()
        
        create_admin_log(
            request=request,
            action_type='update',
            model_name='Vendor',
            object_id=vendor.id,
            object_repr=str(vendor),
            details={'status': 'active', 'is_verified': True}
        )
        
        serializer = self.get_serializer(vendor)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get all products for a specific brand"""
        vendor = self.get_object()
        from products.models import Product
        products = Product.objects.filter(vendor=vendor).select_related('category', 'subcategory')
        serializer = AdminProductListSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        """Get all orders for a specific brand"""
        vendor = self.get_object()
        from orders.models import Order, OrderItem
        orders = Order.objects.filter(items__vendor=vendor).distinct().order_by('-created_at')
        serializer = AdminOrderListSerializer(orders, many=True)
        return Response(serializer.data)


# ==================== Media Management Views ====================
class AdminMediaViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for media management"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminMediaSerializer
    
    def get_queryset(self):
        """Only show media uploaded by admin users (not sellers)"""
        queryset = Media.objects.filter(uploaded_by_user__isnull=False).order_by('-created_at')
        search = self.request.query_params.get('search', None)
        
        if search:
            queryset = queryset.filter(
                Q(file_name__icontains=search) |
                Q(alt_text__icontains=search) |
                Q(description__icontains=search) |
                Q(uploaded_by_user__email__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['post'], url_path='upload')
    def upload_media(self, request):
        """Upload image to Cloudinary"""
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if image_file.content_type not in allowed_types:
            return Response(
                {'error': 'Invalid file type. Only images are allowed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (max 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'File size too large. Maximum size is 10MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            import cloudinary.uploader
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                image_file,
                folder='admin_media',
                resource_type='image'
            )
            
            # Create Media record
            media = Media(
                uploaded_by_user=request.user,
                cloudinary_url=upload_result['secure_url'],
                cloudinary_public_id=upload_result['public_id'],
                file_name=image_file.name,
                file_size=image_file.size,
                mime_type=image_file.content_type,
                alt_text=request.data.get('alt_text', ''),
                description=request.data.get('description', '')
            )
            media.full_clean()  # Validate model
            media.save()
            
            serializer = AdminMediaSerializer(media)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """Delete media from Cloudinary and database"""
        media = self.get_object()
        
        # Only allow deletion of own uploads
        if media.uploaded_by_user != request.user:
            return Response(
                {'error': 'You can only delete your own uploads'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            import cloudinary.uploader
            
            # Delete from Cloudinary if public_id exists
            if media.cloudinary_public_id:
                try:
                    cloudinary.uploader.destroy(media.cloudinary_public_id)
                except Exception as e:
                    # Log error but continue with database deletion
                    print(f"Cloudinary deletion error: {str(e)}")
            
            # Delete from database
            media.delete()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            return Response(
                {'error': f'Deletion failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==================== Packaging Feedback Views ====================
class AdminPackagingFeedbackViewSet(AdminLoggingMixin, viewsets.ModelViewSet):
    """Admin viewset for packaging feedback management"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminPackagingFeedbackSerializer
    
    def get_queryset(self):
        queryset = PackagingFeedback.objects.all().select_related('user', 'reviewed_by').order_by('-created_at')
        search = self.request.query_params.get('search', None)
        status_filter = self.request.query_params.get('status', None)
        feedback_type = self.request.query_params.get('feedback_type', None)
        
        if search:
            queryset = queryset.filter(
                Q(message__icontains=search) |
                Q(user__email__icontains=search) |
                Q(email__icontains=search) |
                Q(name__icontains=search) |
                Q(order_id__icontains=search)
            )
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if feedback_type:
            queryset = queryset.filter(feedback_type=feedback_type)
        
        return queryset
    
    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """Update feedback status"""
        feedback = self.get_object()
        new_status = request.data.get('status')
        admin_notes = request.data.get('admin_notes', '')
        
        if new_status not in dict(PackagingFeedback.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        feedback.status = new_status
        if admin_notes:
            feedback.admin_notes = admin_notes
        if new_status in ['reviewed', 'resolved']:
            feedback.reviewed_by = request.user
            feedback.reviewed_at = timezone.now()
        feedback.save()
        
        serializer = self.get_serializer(feedback)
        return Response(serializer.data)
