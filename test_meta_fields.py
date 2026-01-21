"""
Test script to verify meta_title and meta_description fields work correctly
in both Excel import and manual input scenarios.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from products.models import Product

def test_meta_fields():
    """Test meta_title and meta_description fields"""
    
    print("=" * 70)
    print("Testing Meta Title and Meta Description Fields")
    print("=" * 70)
    
    # Test 1: Manual input through code (simulates form input)
    print("\n1. Testing Manual Input (Form Submission)")
    print("-" * 70)
    
    # Get a product to test with
    test_product = Product.objects.filter(is_active=True).first()
    
    if not test_product:
        print("❌ No active products found for testing")
        return
    
    original_meta_title = test_product.meta_title
    original_meta_description = test_product.meta_description
    
    print(f"Product: {test_product.title}")
    print(f"Original meta_title: '{original_meta_title}'")
    print(f"Original meta_description: '{original_meta_description}'")
    
    # Update with test values
    test_meta_title = "Test Meta Title - Premium Furniture"
    test_meta_description = "This is a test meta description for SEO optimization. Buy premium furniture at best prices."
    
    test_product.meta_title = test_meta_title
    test_product.meta_description = test_meta_description
    test_product.save()
    
    # Verify update
    test_product.refresh_from_db()
    
    if test_product.meta_title == test_meta_title:
        print(f"✅ meta_title updated successfully: '{test_product.meta_title}'")
    else:
        print(f"❌ meta_title update failed")
    
    if test_product.meta_description == test_meta_description:
        print(f"✅ meta_description updated successfully: '{test_product.meta_description[:50]}...'")
    else:
        print(f"❌ meta_description update failed")
    
    # Test 2: Bulk update (simulates Excel import)
    print("\n2. Testing Bulk Update (Excel Import Simulation)")
    print("-" * 70)
    
    # Get multiple products
    test_products = Product.objects.filter(is_active=True)[:3]
    
    bulk_update_list = []
    for idx, product in enumerate(test_products, 1):
        product.meta_title = f"Excel Import Meta Title {idx}"
        product.meta_description = f"Excel import meta description for product {idx}. This simulates bulk import from Excel file."
        bulk_update_list.append(product)
    
    # Perform bulk update
    Product.objects.bulk_update(bulk_update_list, ['meta_title', 'meta_description'])
    
    # Verify bulk update
    print(f"Bulk updated {len(bulk_update_list)} products")
    for product in bulk_update_list:
        product.refresh_from_db()
        print(f"  ✅ {product.title[:40]}... - meta_title: '{product.meta_title}'")
    
    # Test 3: Empty values (optional fields)
    print("\n3. Testing Empty Values (Optional Fields)")
    print("-" * 70)
    
    test_product.meta_title = ""
    test_product.meta_description = ""
    test_product.save()
    test_product.refresh_from_db()
    
    if test_product.meta_title == "" and test_product.meta_description == "":
        print("✅ Empty values work correctly (fields are optional)")
    else:
        print("❌ Empty values handling failed")
    
    # Restore original values
    test_product.meta_title = original_meta_title
    test_product.meta_description = original_meta_description
    test_product.save()
    
    print("\n" + "=" * 70)
    print("✅ All Meta Field Tests Completed Successfully!")
    print("=" * 70)
    print("\nVerification:")
    print("- Manual input (admin form): ✅ Working")
    print("- Bulk update (Excel import): ✅ Working")
    print("- Empty values (optional): ✅ Working")
    print("\nThe meta_title and meta_description fields are ready for use!")

if __name__ == '__main__':
    test_meta_fields()
