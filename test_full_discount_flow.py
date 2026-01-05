"""Test the complete discount filter flow"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.request import Request
from products.views import ProductListView
from products.models import Product, ProductVariant

print("=" * 80)
print("TESTING COMPLETE DISCOUNT FILTER FLOW")
print("=" * 80)

# Test 1: Check ProductFilter
print("\n1. Testing ProductFilter (product-level filtering)")
print("-" * 80)

from products.filters import ProductFilter

products = Product.objects.filter(is_active=True)
print(f"Total active products: {products.count()}")

# Apply discount filter
filter_instance = ProductFilter({'min_discount': '50'}, queryset=products)
filtered_products = filter_instance.qs

print(f"Products after ProductFilter with min_discount=50: {filtered_products.count()}")

for product in filtered_products:
    print(f"  - {product.title[:50]}")
    # Count variants with 50%+ discount
    variants_50plus = 0
    for v in product.variants.filter(is_active=True):
        disc = 0
        if v.discount_percentage:
            disc = v.discount_percentage
        elif v.old_price and v.price and float(v.old_price) > 0:
            disc = ((float(v.old_price) - float(v.price)) / float(v.old_price)) * 100
        if disc >= 50:
            variants_50plus += 1
    print(f"    Has {variants_50plus} variants with 50%+ discount")

# Test 2: Test full API request
print("\n\n2. Testing Full API Request (with variant expansion)")
print("-" * 80)

rf = RequestFactory()
django_request = rf.get('/api/products/', {'min_discount': '50', 'expand_variants': 'true', 'page_size': '1000'})
request = Request(django_request)

view = ProductListView()
view.request = request
view.format_kwarg = None
view.kwargs = {}
view.action = 'list'

try:
    response = view.list(request)
    data = response.data
    
    if 'results' in data:
        results = data['results']
        print(f"API returned {len(results)} results (expanded variants)")
        print(f"Total count: {data.get('count', 'N/A')}")
        
        if len(results) > 0:
            print("\nFirst 5 results:")
            for i, item in enumerate(results[:5], 1):
                disc = item.get('discount_percentage', 0)
                print(f"  {i}. {item['title'][:60]}")
                print(f"     Discount: {disc}%, Price: ₹{item['price']}, Old Price: ₹{item.get('old_price', 'N/A')}")
        else:
            print("\n⚠️ API RETURNED ZERO RESULTS - THIS IS THE BUG!")
            print("Even though we have products with 50%+ discount variants...")
    else:
        print("Response structure:", data.keys() if hasattr(data, 'keys') else type(data))
        
except Exception as e:
    print(f"ERROR during API call: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
