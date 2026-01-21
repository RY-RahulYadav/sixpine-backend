"""
Test script to verify order item images are displayed correctly
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from orders.models import Order
from orders.serializers import OrderDetailSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 80)
print("ORDER IMAGE DISPLAY TEST")
print("=" * 80)

# Get the latest order
orders = Order.objects.all().order_by('-created_at')[:3]

if not orders:
    print("\n❌ No orders found in database")
    sys.exit(1)

for order in orders:
    print(f"\n{'='*80}")
    print(f"Order ID: {order.order_id}")
    print(f"Customer: {order.user.email}")
    print(f"Status: {order.status}")
    print(f"Total: ₹{order.total_amount}")
    print(f"Items Count: {order.items.count()}")
    print(f"\nOrder Items:")
    print("-" * 80)
    
    for item in order.items.all():
        print(f"\n  Product: {item.product.title}")
        print(f"  Product ID: {item.product.id}")
        
        # Check variant
        if item.variant:
            print(f"  Variant: {item.variant.title if item.variant.title else 'N/A'}")
            print(f"  Variant ID: {item.variant.id}")
            print(f"  Variant Color: {item.variant.color.name if item.variant.color else 'N/A'}")
            print(f"  Variant Size: {item.variant.size or 'N/A'}")
            print(f"  Variant Image: {item.variant.image or 'None'}")
        else:
            print(f"  Variant: None")
        
        # Check product images
        print(f"  Product parent_main_image: {item.product.parent_main_image or 'None'}")
        print(f"  Product main_image: {item.product.main_image or 'None'}")
        
        # Check what image will be used (using serializer logic)
        from orders.serializers import OrderItemSerializer
        serializer = OrderItemSerializer(item)
        image_url = serializer.get_product_image(item)
        
        print(f"  ✅ Image URL (from serializer): {image_url}")
        
        if image_url:
            print(f"  🎯 Image found: YES")
        else:
            print(f"  ❌ Image found: NO - This needs attention!")
    
    print("\n" + "=" * 80)
    
    # Serialize the full order to see the JSON output
    serializer = OrderDetailSerializer(order)
    order_data = serializer.data
    
    print("\nSerialized Order Items (with images):")
    print("-" * 80)
    for item_data in order_data.get('items', []):
        product_title = item_data.get('product', {}).get('title', 'N/A')
        product_image = item_data.get('product_image', 'N/A')
        print(f"  - {product_title}")
        print(f"    Image: {product_image}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("\n✅ If images are shown above, the order display will work correctly!")
print("   The frontend should use the 'product_image' field from order items.")
