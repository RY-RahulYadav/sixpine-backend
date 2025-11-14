from decimal import Decimal
from admin_api.models import GlobalSettings


def get_platform_fee_percentage(payment_method):
    """Get platform fee percentage based on payment method
    
    Handles both Razorpay format (card, netbanking, upi, wallet) 
    and internal format (CC, NB, UPI, CARD, NET_BANKING, etc.)
    """
    if not payment_method:
        return Decimal('0.00')
    
    # Normalize payment method to lowercase first for Razorpay format
    payment_method_lower = str(payment_method).lower()
    payment_method_upper = str(payment_method).upper()
    
    # Handle Razorpay format (card, netbanking, upi, wallet)
    if payment_method_lower in ['card']:
        fee_percentage = Decimal(str(GlobalSettings.get_setting('platform_fee_card', '2.36')))
    elif payment_method_lower in ['netbanking', 'net_banking']:
        fee_percentage = Decimal(str(GlobalSettings.get_setting('platform_fee_netbanking', '2.36')))
    elif payment_method_lower in ['upi']:
        fee_percentage = Decimal(str(GlobalSettings.get_setting('platform_fee_upi', '0.00')))
    # Handle internal format (CC, CARD, NB, UPI, NET_BANKING, etc.)
    elif payment_method_upper in ['UPI']:
        fee_percentage = Decimal(str(GlobalSettings.get_setting('platform_fee_upi', '0.00')))
    elif payment_method_upper in ['CC', 'CARD', 'RAZORPAY']:
        # CC = Credit Card, CARD = Card, RAZORPAY = Razorpay (all use card fee)
        fee_percentage = Decimal(str(GlobalSettings.get_setting('platform_fee_card', '2.36')))
    elif payment_method_upper in ['NB', 'NET_BANKING', 'NETBANKING']:
        # NB = Net Banking (short form)
        fee_percentage = Decimal(str(GlobalSettings.get_setting('platform_fee_netbanking', '2.36')))
    elif payment_method_upper in ['COD']:
        fee_percentage = Decimal(str(GlobalSettings.get_setting('platform_fee_cod', '0.00')))
    else:
        # Default to 0 for unknown payment methods
        fee_percentage = Decimal('0.00')
    
    return fee_percentage


def calculate_platform_fee(subtotal, payment_method):
    """Calculate platform fee amount based on subtotal and payment method"""
    fee_percentage = get_platform_fee_percentage(payment_method)
    platform_fee = (subtotal * fee_percentage) / Decimal('100.00')
    return platform_fee.quantize(Decimal('0.01'))


def calculate_order_totals(subtotal, payment_method=None):
    """Calculate all order totals including platform fee and tax"""
    from admin_api.models import GlobalSettings
    
    # Get tax rate
    tax_rate = Decimal(str(GlobalSettings.get_setting('tax_rate', '5.00')))
    
    # Calculate tax
    tax_amount = (subtotal * tax_rate) / Decimal('100.00')
    tax_amount = tax_amount.quantize(Decimal('0.01'))
    
    # Calculate platform fee (only for non-COD payments)
    platform_fee = Decimal('0.00')
    if payment_method:
        platform_fee = calculate_platform_fee(subtotal, payment_method)
    
    # Shipping cost is now 0 (removed)
    shipping_cost = Decimal('0.00')
    
    # Calculate total
    total_amount = subtotal + tax_amount + platform_fee + shipping_cost
    total_amount = total_amount.quantize(Decimal('0.01'))
    
    return {
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'platform_fee': platform_fee,
        'shipping_cost': shipping_cost,
        'total_amount': total_amount
    }

