"""Debug discount filter - check why it returns no products"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from products.models import ProductVariant, Product
from django.db.models import Q

print("=" * 80)
print("TESTING DISCOUNT FILTER LOGIC")
print("=" * 80)

# Simulate what the filter does
min_discount = 50

variants = ProductVariant.objects.filter(is_active=True)
print(f"\nTotal active variants: {variants.count()}")

matching_variants = []

for variant in variants:
    # Calculate discount same way as in views.py
    variant_discount = 0
    
    if variant.discount_percentage:
        variant_discount = float(variant.discount_percentage)
    elif variant.old_price and variant.price and float(variant.old_price) > 0:
        variant_discount = ((float(variant.old_price) - float(variant.price)) / float(variant.old_price)) * 100
    
    variant_discount = round(variant_discount, 2)
    
    # Check if meets threshold
    if variant_discount >= min_discount:
        matching_variants.append((variant, variant_discount))

print(f"Variants with discount >= {min_discount}%: {len(matching_variants)}")

if len(matching_variants) > 0:
    print("\nFirst 10 matching variants:")
    for variant, disc in matching_variants[:10]:
        print(f"  ID: {variant.id}, Discount: {disc}%, Price: {variant.price}, Old: {variant.old_price}")
        print(f"  Title: {variant.title[:60]}")
        print(f"  Product: {variant.product.title[:50]}")
        print()
else:
    print("\n⚠️ NO VARIANTS FOUND WITH 50%+ DISCOUNT!")
    print("This explains why the filter returns 'no products'")
    
print("=" * 80)
print("CHECKING PRODUCT QUERYSET FILTERING")
print("=" * 80)

# Check if the base product queryset is correct
products = Product.objects.filter(is_active=True)
print(f"\nTotal active products: {products.count()}")

# Check products with variants
products_with_variants = []
for product in products[:20]:
    variants = product.variants.filter(is_active=True)
    if variants.exists():
        products_with_variants.append((product, variants.count()))

print(f"Products with variants (first 20): {len(products_with_variants)}")
for product, v_count in products_with_variants[:5]:
    print(f"  Product: {product.title[:50]}, Variants: {v_count}")
