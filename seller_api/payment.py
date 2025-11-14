from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q, F, DecimalField
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from orders.models import Order, OrderItem
from .permissions import IsVendorUser


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVendorUser])
def seller_payment_dashboard(request):
    """Get payment dashboard stats for seller"""
    try:
        vendor = request.user.vendor_profile
        
        # Get all order items for this vendor
        vendor_order_items = OrderItem.objects.filter(vendor=vendor)
        
        # Get orders that contain vendor's products
        vendor_orders = Order.objects.filter(items__vendor=vendor).distinct()
        
        # Total order value (sum of total_amount including tax for orders containing vendor's products)
        # Calculate vendor's share of total amount customer paid
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
        
        # Calculate platform fees and taxes for delivered orders only
        # Platform fee is stored in Order model
        # Tax is calculated on subtotal
        total_platform_fees = Decimal('0.00')
        total_taxes = Decimal('0.00')
        total_net_revenue = Decimal('0.00')
        
        # Get tax rate from global settings
        from admin_api.models import GlobalSettings
        tax_rate = Decimal(str(GlobalSettings.get_setting('tax_rate', '5.00')))
        
        # Calculate for delivered order items only
        delivered_vendor_order_items = vendor_order_items.filter(order__status='delivered')
        for order_item in delivered_vendor_order_items:
            item_subtotal = order_item.price * order_item.quantity
            
            # Get order to access platform_fee
            order = order_item.order
            
            # Calculate platform fee percentage for this order
            # Platform fee is already calculated and stored in order
            # We need to calculate vendor's share of platform fee
            # Platform fee is on total order, so we need to calculate vendor's proportional share
            order_total_items = order.items.aggregate(
                total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
            )['total'] or Decimal('0.00')
            
            if order_total_items > 0:
                # Vendor's share of platform fee = (vendor_items_value / order_total) * platform_fee
                vendor_share_platform_fee = (item_subtotal / order_total_items) * (order.platform_fee or Decimal('0.00'))
                total_platform_fees += vendor_share_platform_fee
                
                # Tax is calculated on subtotal (before platform fee)
                # Tax rate is applied to the order subtotal, so calculate vendor's share
                order_subtotal = order.subtotal
                if order_subtotal > 0:
                    vendor_share_tax = (item_subtotal / order_subtotal) * (order.tax_amount or Decimal('0.00'))
                    total_taxes += vendor_share_tax
                else:
                    # Fallback: calculate tax directly on vendor's item
                    vendor_share_tax = (item_subtotal * tax_rate) / Decimal('100.00')
                    total_taxes += vendor_share_tax
            
            # Net revenue = item value - platform fee share - tax share
            vendor_share_platform_fee = (item_subtotal / order_total_items) * (order.platform_fee or Decimal('0.00')) if order_total_items > 0 else Decimal('0.00')
            vendor_share_tax = (item_subtotal / order_subtotal) * (order.tax_amount or Decimal('0.00')) if order_subtotal > 0 else (item_subtotal * tax_rate) / Decimal('100.00')
            net_revenue_item = item_subtotal - vendor_share_platform_fee - vendor_share_tax
            total_net_revenue += net_revenue_item
        
        # Orders by status
        orders_by_status = vendor_orders.values('status').annotate(
            count=Count('id'),
            revenue=Sum('items__price', filter=Q(items__vendor=vendor))
        )
        
        # Recent orders with payment breakdown
        recent_orders = vendor_orders.order_by('-created_at')[:10]
        recent_orders_data = []
        
        for order in recent_orders:
            # Get vendor's items in this order
            vendor_items = order.items.filter(vendor=vendor)
            vendor_items_subtotal = sum(item.price * item.quantity for item in vendor_items)
            
            # Calculate vendor's share of total amount (including tax)
            if order.subtotal > 0:
                vendor_share_ratio = Decimal(str(vendor_items_subtotal)) / order.subtotal
                vendor_order_value = order.total_amount * vendor_share_ratio
            else:
                vendor_order_value = Decimal(str(vendor_items_subtotal))
            
            # Calculate vendor's share of fees
            order_total_items = order.items.aggregate(
                total=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=10, decimal_places=2))
            )['total'] or Decimal('0.00')
            
            vendor_platform_fee = Decimal('0.00')
            vendor_tax = Decimal('0.00')
            
            if order_total_items > 0:
                vendor_platform_fee = (vendor_order_value / order_total_items) * (order.platform_fee or Decimal('0.00'))
                order_subtotal = order.subtotal
                if order_subtotal > 0:
                    vendor_tax = (vendor_order_value / order_subtotal) * (order.tax_amount or Decimal('0.00'))
                else:
                    vendor_tax = (vendor_order_value * tax_rate) / Decimal('100.00')
            
            vendor_net_revenue = vendor_order_value - vendor_platform_fee - vendor_tax
            
            recent_orders_data.append({
                'id': order.id,
                'order_id': str(order.order_id),
                'date': order.created_at.strftime('%Y-%m-%d'),
                'customer_name': order.user.get_full_name() or order.user.username,
                'status': order.status,
                'payment_status': order.payment_status,
                'order_value': float(vendor_order_value),
                'platform_fee': float(vendor_platform_fee),
                'tax': float(vendor_tax),
                'net_revenue': float(vendor_net_revenue),
                'items_count': vendor_items.count()
            })
        
        # Monthly breakdown
        this_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month = (this_month - timedelta(days=1)).replace(day=1)
        
        this_month_orders = vendor_orders.filter(created_at__gte=this_month)
        last_month_orders = vendor_orders.filter(created_at__gte=last_month, created_at__lt=this_month)
        
        this_month_value = sum(
            item.price * item.quantity 
            for order in this_month_orders 
            for item in order.items.filter(vendor=vendor)
        )
        last_month_value = sum(
            item.price * item.quantity 
            for order in last_month_orders 
            for item in order.items.filter(vendor=vendor)
        )
        
        return Response({
            'success': True,
            'stats': {
                'total_order_value': float(total_order_value),
                'total_platform_fees': float(total_platform_fees),
                'total_taxes': float(total_taxes),
                'total_net_revenue': float(total_net_revenue),
                'total_orders': vendor_orders.count(),
                'this_month_value': float(this_month_value),
                'last_month_value': float(last_month_value),
                'orders_by_status': [
                    {
                        'status': item['status'],
                        'count': item['count']
                    }
                    for item in orders_by_status
                ],
                'recent_orders': recent_orders_data
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

