"""
Reset Orders and Profits Script
=================================
This script resets all order-related data and statistics to zero.

CAUTION: This will permanently delete all order data!

What this script does:
- Deletes all orders, order items, order status history, order notes
- Deletes all return requests
- Resets payment statuses and tracking information
- Clears order-related admin logs (optional)
- Provides a comprehensive summary of deleted data

Usage:
    python reset_orders_and_profits.py
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from django.db import transaction
from orders.models import Order, OrderItem, OrderStatusHistory, OrderNote, ReturnRequest, Address
from admin_api.models import AdminLog
from django.contrib.auth import get_user_model

User = get_user_model()


def print_separator():
    """Print a visual separator"""
    print("\n" + "=" * 80 + "\n")


def get_current_stats():
    """Get current order statistics before reset"""
    stats = {
        'total_orders': Order.objects.count(),
        'total_order_items': OrderItem.objects.count(),
        'total_order_value': Order.objects.aggregate(
            total=django.db.models.Sum('total_amount')
        )['total'] or Decimal('0.00'),
        'orders_by_status': {},
        'orders_by_payment_status': {},
        'orders_by_payment_method': {},
        'order_status_history': OrderStatusHistory.objects.count(),
        'order_notes': OrderNote.objects.count(),
        'return_requests': ReturnRequest.objects.count(),
        'order_admin_logs': AdminLog.objects.filter(model_name='Order').count(),
    }
    
    # Count orders by status
    for status, _ in Order.STATUS_CHOICES:
        count = Order.objects.filter(status=status).count()
        if count > 0:
            stats['orders_by_status'][status] = count
    
    # Count orders by payment status
    for payment_status, _ in Order.PAYMENT_STATUS_CHOICES:
        count = Order.objects.filter(payment_status=payment_status).count()
        if count > 0:
            stats['orders_by_payment_status'][payment_status] = count
    
    # Count orders by payment method
    for payment_method, _ in Order.PAYMENT_METHOD_CHOICES:
        count = Order.objects.filter(payment_method=payment_method).count()
        if count > 0:
            stats['orders_by_payment_method'][payment_method] = count
    
    return stats


def display_stats(stats, title="Current Statistics"):
    """Display statistics in a formatted way"""
    print_separator()
    print(f"📊 {title}")
    print_separator()
    
    print(f"Total Orders: {stats['total_orders']}")
    print(f"Total Order Items: {stats['total_order_items']}")
    print(f"Total Order Value: ₹{stats['total_order_value']:,.2f}")
    
    if stats['orders_by_status']:
        print("\nOrders by Status:")
        for status, count in stats['orders_by_status'].items():
            print(f"  - {status.title()}: {count}")
    
    if stats['orders_by_payment_status']:
        print("\nOrders by Payment Status:")
        for payment_status, count in stats['orders_by_payment_status'].items():
            print(f"  - {payment_status.title()}: {count}")
    
    if stats['orders_by_payment_method']:
        print("\nOrders by Payment Method:")
        for payment_method, count in stats['orders_by_payment_method'].items():
            print(f"  - {payment_method}: {count}")
    
    print(f"\nOrder Status History Records: {stats['order_status_history']}")
    print(f"Order Notes: {stats['order_notes']}")
    print(f"Return Requests: {stats['return_requests']}")
    print(f"Order-related Admin Logs: {stats['order_admin_logs']}")


def reset_all_orders():
    """Reset all orders and related data"""
    print_separator()
    print("🔄 RESET ORDERS AND PROFITS")
    print_separator()
    
    # Get current stats before deletion
    print("Collecting current statistics...")
    before_stats = get_current_stats()
    display_stats(before_stats, "Statistics Before Reset")
    
    if before_stats['total_orders'] == 0:
        print_separator()
        print("✅ No orders to reset. Database is already clean!")
        print_separator()
        return
    
    # Start reset immediately without confirmation
    print_separator()
    print("🚀 Starting reset process...\n")
    
    try:
        with transaction.atomic():
            deletion_summary = {}
            
            # Delete return requests first (foreign key to OrderItem)
            print("Deleting return requests...")
            return_count = ReturnRequest.objects.count()
            ReturnRequest.objects.all().delete()
            deletion_summary['return_requests'] = return_count
            print(f"  ✓ Deleted {return_count} return requests")
            
            # Delete order status history
            print("Deleting order status history...")
            status_history_count = OrderStatusHistory.objects.count()
            OrderStatusHistory.objects.all().delete()
            deletion_summary['order_status_history'] = status_history_count
            print(f"  ✓ Deleted {status_history_count} status history records")
            
            # Delete order notes
            print("Deleting order notes...")
            notes_count = OrderNote.objects.count()
            OrderNote.objects.all().delete()
            deletion_summary['order_notes'] = notes_count
            print(f"  ✓ Deleted {notes_count} order notes")
            
            # Delete order items (will be cascaded, but doing explicitly for clarity)
            print("Deleting order items...")
            items_count = OrderItem.objects.count()
            OrderItem.objects.all().delete()
            deletion_summary['order_items'] = items_count
            print(f"  ✓ Deleted {items_count} order items")
            
            # Delete orders
            print("Deleting orders...")
            orders_count = Order.objects.count()
            total_value = Order.objects.aggregate(
                total=django.db.models.Sum('total_amount')
            )['total'] or Decimal('0.00')
            Order.objects.all().delete()
            deletion_summary['orders'] = orders_count
            deletion_summary['total_order_value'] = total_value
            print(f"  ✓ Deleted {orders_count} orders (Total value: ₹{total_value:,.2f})")
            
            # Optional: Delete order-related admin logs
            print("\nDeleting order-related admin logs...")
            order_logs_count = AdminLog.objects.filter(model_name='Order').count()
            AdminLog.objects.filter(model_name='Order').delete()
            deletion_summary['order_admin_logs'] = order_logs_count
            print(f"  ✓ Deleted {order_logs_count} admin log entries")
            
            # Also delete OrderItem-related logs
            item_logs_count = AdminLog.objects.filter(model_name='OrderItem').count()
            AdminLog.objects.filter(model_name='OrderItem').delete()
            deletion_summary['item_admin_logs'] = item_logs_count
            print(f"  ✓ Deleted {item_logs_count} order item log entries")
            
        # Verify reset
        print("\n🔍 Verifying reset...")
        after_stats = get_current_stats()
        
        if after_stats['total_orders'] == 0:
            print_separator()
            print("✅ RESET COMPLETED SUCCESSFULLY!")
            print_separator()
            
            print("\n📋 Deletion Summary:")
            print(f"  • Orders deleted: {deletion_summary['orders']}")
            print(f"  • Order items deleted: {deletion_summary['order_items']}")
            print(f"  • Status history records deleted: {deletion_summary['order_status_history']}")
            print(f"  • Order notes deleted: {deletion_summary['order_notes']}")
            print(f"  • Return requests deleted: {deletion_summary['return_requests']}")
            print(f"  • Admin logs deleted: {deletion_summary['order_admin_logs'] + deletion_summary['item_admin_logs']}")
            print(f"  • Total order value cleared: ₹{deletion_summary['total_order_value']:,.2f}")
            
            print_separator()
            print("📊 Impact on Dashboard Statistics:")
            print("  • Total Order Value: ₹0.00")
            print("  • Net Profit (Sellers): ₹0.00")
            print("  • Sixpine Profit: ₹0.00")
            print("  • Total Net Revenue: ₹0.00")
            print("  • Total Orders: 0")
            print("  • Delivered Orders: 0")
            print("  • Orders Placed: 0")
            print("  • COD Orders: 0")
            print("  • Online Payment Orders: 0")
            print_separator()
            
            print("\n💡 Next Steps:")
            print("  1. Refresh your admin dashboard to see updated statistics")
            print("  2. All order-related data has been cleared")
            print("  3. Product inventory has NOT been affected")
            print("  4. User accounts and addresses remain intact")
            print_separator()
        else:
            print("❌ Verification failed! Some orders may still exist.")
            display_stats(after_stats, "Statistics After Reset")
            
    except Exception as e:
        print(f"\n❌ ERROR during reset: {str(e)}")
        print("Transaction rolled back. No data was deleted.")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import django.db.models
    reset_all_orders()
