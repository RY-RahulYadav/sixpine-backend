"""
Verify Razorpay Keys Configuration
Run: python verify_razorpay_keys.py
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from django.conf import settings
import razorpay

def verify_razorpay_keys():
    print("="*70)
    print("  RAZORPAY KEYS VERIFICATION")
    print("="*70)
    
    # Get keys from settings
    key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
    
    print(f"\n[1] Checking Environment Variables:")
    print(f"   RAZORPAY_KEY_ID: {'✓ Set' if key_id else '✗ Missing'} ({len(key_id)} chars)")
    print(f"   RAZORPAY_KEY_SECRET: {'✓ Set' if key_secret else '✗ Missing'} ({len(key_secret)} chars)")
    
    # Check key lengths
    if len(key_id) < 20 or len(key_id) > 30:
        print(f"   ⚠ WARNING: Key ID length ({len(key_id)}) seems unusual (typically 20-24 chars)")
    if len(key_secret) < 30 or len(key_secret) > 50:
        print(f"   ⚠ WARNING: Secret length ({len(key_secret)}) seems unusual (typically 32+ chars)")
    
    if not key_id or not key_secret:
        print("\n[ERROR] Missing Razorpay keys! Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET")
        return False
    
    # Check key format
    print(f"\n[2] Checking Key Format:")
    print(f"   Key ID (first 12 chars): {key_id[:12]}..." if len(key_id) > 12 else f"   Key ID: {key_id}")
    print(f"   Key Secret (first 12 chars): {key_secret[:12]}..." if len(key_secret) > 12 else f"   Key Secret: {key_secret}")
    
    # Check for whitespace
    if key_id != key_id.strip() or key_secret != key_secret.strip():
        print(f"\n[WARNING] ⚠ Keys contain whitespace! This can cause authentication errors.")
        print(f"   Please remove any leading/trailing spaces from your keys")
        key_id = key_id.strip()
        key_secret = key_secret.strip()
    
    if key_id.startswith('rzp_test_'):
        print(f"   Key ID: Test mode ✓")
        key_type = 'test'
    elif key_id.startswith('rzp_live_'):
        print(f"   Key ID: Live mode ✓")
        key_type = 'live'
    else:
        print(f"   Key ID: ⚠ Unknown format - should start with 'rzp_test_' or 'rzp_live_'")
        key_type = 'unknown'
    
    if len(key_secret) > 0 and not key_secret.startswith('rzp_'):
        print(f"   Key Secret: ✓ (Razorpay secrets don't start with 'rzp_')")
        secret_type = key_type  # Assume same type as key ID
    else:
        secret_type = 'unknown'
        print(f"   Key Secret: ⚠ Unexpected format")
    
    # Check if keys might be swapped
    if key_id.startswith('rzp_') and key_secret.startswith('rzp_'):
        print(f"\n[ERROR] ⚠ Keys might be SWAPPED!")
        print(f"   Key ID should start with 'rzp_' but Secret should NOT")
        print(f"   Please check: Key ID should be 'rzp_test_...' or 'rzp_live_...'")
        print(f"   Secret should be a long string WITHOUT 'rzp_' prefix")
        return False
    
    # Test Razorpay connection
    print(f"\n[3] Testing Razorpay Connection:")
    try:
        # Strip whitespace before testing
        key_id_clean = key_id.strip()
        key_secret_clean = key_secret.strip()
        
        client = razorpay.Client(auth=(key_id_clean, key_secret_clean))
        print(f"   ✓ Client initialized successfully!")
        
        # Try creating a test order to validate the keys
        print(f"\n[4] Testing Order Creation:")
        try:
            test_order = client.order.create({
                'amount': 100,  # 1 rupee in paise
                'currency': 'INR',
                'receipt': 'test_verification_' + str(int(__import__('time').time()))
            })
            print(f"   ✓ Test order created successfully!")
            print(f"   Order ID: {test_order['id']}")
            print(f"   Amount: {test_order['amount']} paise ({test_order['amount']/100} INR)")
            
            # Verify we can fetch the order
            try:
                fetched_order = client.order.fetch(test_order['id'])
                print(f"   ✓ Order verification successful!")
            except Exception as e:
                print(f"   ⚠ Could not fetch order (may be normal): {str(e)}")
                
        except razorpay.errors.BadRequestError as e:
            error_msg = str(e)
            print(f"   ✗ Failed to create test order")
            print(f"   Error: {error_msg}")
            
            if 'authentication' in error_msg.lower() or 'invalid' in error_msg.lower():
                print(f"\n   [DIAGNOSIS] Authentication failed possible causes:")
                print(f"   1. Key ID and Secret don't match (from different accounts)")
                print(f"   2. Keys are swapped (ID used as Secret or vice versa)")
                print(f"   3. Keys contain whitespace or special characters")
                print(f"   4. Keys are expired or revoked in Razorpay dashboard")
                print(f"   5. Using test keys in live mode or vice versa")
            return False
        except razorpay.errors.ServerError as e:
            print(f"   ✗ Razorpay server error: {str(e)}")
            print(f"   This might be temporary - try again in a few minutes")
            return False
        except Exception as e:
            print(f"   ✗ Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        print(f"\n[SUCCESS] All Razorpay keys are valid and working!")
        return True
        
    except razorpay.errors.BadRequestError as e:
        error_msg = str(e)
        print(f"   ✗ Connection failed: {error_msg}")
        if 'invalid' in error_msg.lower() or 'authentication' in error_msg.lower():
            print("\n   [ERROR] Invalid Razorpay keys! Please check:")
            print("   1. Key ID and Secret are correct")
            print("   2. Both keys are from the same Razorpay account")
            print("   3. Keys are not expired or revoked")
        return False
    except Exception as e:
        print(f"   ✗ Connection error: {str(e)}")
        return False

if __name__ == '__main__':
    try:
        success = verify_razorpay_keys()
        if not success:
            print("\n" + "="*70)
            print("  TROUBLESHOOTING:")
            print("="*70)
            print("1. Check your .env file or environment variables")
            print("2. Ensure both RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are set")
            print("3. Make sure keys are from the same Razorpay account (test or live)")
            print("4. Restart Django server after updating keys:")
            print("   - Stop server (Ctrl+C)")
            print("   - python manage.py runserver")
            print("5. Clear browser cache if frontend shows old key")
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

