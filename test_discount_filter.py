"""Test script to verify discount filtering is working correctly"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from products.models import ProductVariant, Product
from django.db.models import Q

# Test 1: Check variants with discount >= 50%
print("=" * 80)
print("TEST 1: Variants with discount_percentage >= 50%")
print("=" * 80)

variants_50_plus = ProductVariant.objects.filter(
    is_active=True,
    discount_percentage__gte=50
).select_related('product')[:10]

print(f"\nFound {variants_50_plus.count()} variants with discount >= 50%\n")

for variant in variants_50_plus:
    print(f"ID: {variant.id}")
    print(f"Title: {variant.title[:60]}")
    print(f"Product: {variant.product.title[:50]}")
    print(f"Price: ₹{variant.price}, Old Price: ₹{variant.old_price}")
    print(f"Discount: {variant.discount_percentage}%")
    print("-" * 80)

# Test 2: Check calculated discounts
print("\n" + "=" * 80)
print("TEST 2: Variants with calculated discount >= 50% (from old_price and price)")
print("=" * 80)

all_variants = ProductVariant.objects.filter(
    is_active=True,
    old_price__gt=0,
    price__gt=0
).select_related('product')

calculated_50_plus = []
for variant in all_variants[:100]:  # Check first 100
    if variant.old_price and variant.price and float(variant.old_price) > 0:
        calculated_discount = ((float(variant.old_price) - float(variant.price)) / float(variant.old_price)) * 100
        if calculated_discount >= 50:
            calculated_50_plus.append((variant, calculated_discount))

print(f"\nFound {len(calculated_50_plus)} variants (from first 100) with calculated discount >= 50%\n")

for variant, disc in calculated_50_plus[:5]:
    print(f"ID: {variant.id}")
    print(f"Title: {variant.title[:60]}")
    print(f"Price: ₹{variant.price}, Old Price: ₹{variant.old_price}")
    print(f"Stored Discount: {variant.discount_percentage}%")
    print(f"Calculated Discount: {disc:.2f}%")
    print("-" * 80)

# Test 3: Check filter options
print("\n" + "=" * 80)
print("TEST 3: Available discount filter options")
print("=" * 80)

from products.models import Discount
discounts = Discount.objects.filter(is_active=True).order_by('percentage')
print(f"\nAvailable discount options: {list(discounts.values_list('percentage', 'label'))}")

print("\n" + "=" * 80)
print("CONCLUSION:")
print("=" * 80)
print("If you see variants listed above, the discount filter SHOULD be working.")
print("If the frontend isn't showing filtered results, check:")
print("1. Browser console for the API request parameters")
print("2. Network tab to see if min_discount parameter is being sent")
print("3. Backend logs to see if the filter is being applied")
print("=" * 80)
