"""
Order Email Service
Handles email notifications for order confirmations
"""
import logging
from django.conf import settings
from accounts.brevo_email_service import BrevoEmailService

logger = logging.getLogger('orders')


def get_order_confirmation_email_html(order, user):
    """
    Generate HTML content for order confirmation email
    Based on Amazon-style template with Sixpine branding
    
    Args:
        order: Order instance
        user: User instance
    
    Returns:
        str: HTML content for the email
    """
    # Format shipping date
    from datetime import datetime, timedelta
    ship_by_date = datetime.now() + timedelta(days=2)
    ship_by_formatted = ship_by_date.strftime('%d/%m/%Y')
    
    # Build items list HTML
    items_html = ""
    for item in order.items.all():
        # Get product details
        product_name = item.product.title if hasattr(item.product, 'title') else str(item.product)
        
        # Truncate long product names to maintain email design (limit to 45 chars)
        if len(product_name) > 45:
            product_name = product_name[:42] + '...'
        
        quantity = item.quantity
        price = item.price
        
        # Build variant details without labels (just values separated by |)
        variant_details = []
        if item.variant:
            if item.variant.color:
                variant_details.append(item.variant.color.name)
            if item.variant.pattern:
                variant_details.append(item.variant.pattern)
            if item.variant.size:
                variant_details.append(item.variant.size)
            if hasattr(item.variant, 'quality') and item.variant.quality:
                variant_details.append(item.variant.quality)
        
        variant_info = " | ".join(variant_details) if variant_details else ""
        
        items_html += f"""
        <tr>
            <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;">
                <strong>{product_name}</strong>
                {f'<br><span style="color: #666; font-size: 13px;">{variant_info}</span>' if variant_info else ''}
            </td>
            <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0; text-align: center;">
                {quantity}
            </td>
            <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0; text-align: right;">
                ₹{price:.2f}
            </td>
        </tr>
        """
    
    # Calculate totals for display
    subtotal = order.subtotal
    discount = order.coupon_discount
    shipping = order.shipping_cost
    platform_fee = order.platform_fee
    tax = order.tax_amount
    total = order.total_amount
    
    # Build shipping address
    address = order.shipping_address
    shipping_address = f"""{address.full_name}<br>
    {address.street_address}<br>
    {address.city}, {address.state} - {address.postal_code}<br>
    {address.country}<br>
    Phone: {address.phone}"""
    
    # Payment method display
    payment_method_display = dict(order.PAYMENT_METHOD_CHOICES).get(order.payment_method, order.payment_method)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f6f6f6;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f6f6f6;">
            <tr>
                <td align="center" style="padding: 20px 0;">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background-color: #232f3e; padding: 20px 30px;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">sixpine</h1>
                            </td>
                        </tr>
                        
                        <!-- Greeting -->
                        <tr>
                            <td style="padding: 30px 30px 20px 30px;">
                                <p style="margin: 0 0 15px 0; color: #333333; font-size: 16px; line-height: 1.5;">
                                    Congratulations, you have a new order on Sixpine!
                                </p>
                                <p style="margin: 0 0 20px 0; color: #666666; font-size: 14px;">
                                    Please review your order:
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Order Details -->
                        <tr>
                            <td style="padding: 0 30px 30px 30px;">
                                <div style="background-color: #f3f3f3; padding: 20px; border-radius: 4px;">
                                    <h2 style="margin: 0 0 15px 0; color: #111111; font-size: 18px; font-weight: bold;">Order Details</h2>
                                    
                                    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 15px;">
                                        <tr>
                                            <td style="padding: 5px 0; color: #666666; font-size: 14px;">Order ID:</td>
                                            <td style="padding: 5px 0; color: #111111; font-size: 14px; text-align: right; font-weight: bold;">
                                                {order.order_id}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 5px 0; color: #666666; font-size: 14px;">Order date:</td>
                                            <td style="padding: 5px 0; color: #111111; font-size: 14px; text-align: right;">
                                                {order.created_at.strftime('%d/%m/%Y')}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 5px 0; color: #666666; font-size: 14px;">Payment Method:</td>
                                            <td style="padding: 5px 0; color: #111111; font-size: 14px; text-align: right;">
                                                {payment_method_display}
                                            </td>
                                        </tr>
                                    </table>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Items Table -->
                        <tr>
                            <td style="padding: 0 30px 30px 30px;">
                                <h3 style="margin: 0 0 15px 0; color: #111111; font-size: 16px; font-weight: bold;">Items:</h3>
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <thead>
                                        <tr style="border-bottom: 2px solid #e0e0e0;">
                                            <th style="padding: 10px 0; text-align: left; color: #111111; font-size: 14px; font-weight: bold;">Product</th>
                                            <th style="padding: 10px 0; text-align: center; color: #111111; font-size: 14px; font-weight: bold;">Qty</th>
                                            <th style="padding: 10px 0; text-align: right; color: #111111; font-size: 14px; font-weight: bold;">Price</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {items_html}
                                    </tbody>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Pricing Summary -->
                        <tr>
                            <td style="padding: 0 30px 30px 30px;">
                                <table width="100%" cellpadding="0" cellspacing="0" style="border-top: 2px solid #e0e0e0; padding-top: 15px;">
                                    <tr>
                                        <td style="padding: 5px 0; color: #666666; font-size: 14px;">Subtotal:</td>
                                        <td style="padding: 5px 0; color: #111111; font-size: 14px; text-align: right;">₹{subtotal:.2f}</td>
                                    </tr>
                                    {f'''<tr>
                                        <td style="padding: 5px 0; color: #666666; font-size: 14px;">Discount:</td>
                                        <td style="padding: 5px 0; color: #c7511f; font-size: 14px; text-align: right;">-₹{discount:.2f}</td>
                                    </tr>''' if discount > 0 else ''}
                                    <tr>
                                        <td style="padding: 5px 0; color: #666666; font-size: 14px;">Shipping:</td>
                                        <td style="padding: 5px 0; color: #111111; font-size: 14px; text-align: right;">
                                            {'FREE' if shipping == 0 else f'₹{shipping:.2f}'}
                                        </td>
                                    </tr>
                                    {f'''<tr>
                                        <td style="padding: 5px 0; color: #666666; font-size: 14px;">Platform Fee:</td>
                                        <td style="padding: 5px 0; color: #111111; font-size: 14px; text-align: right;">₹{platform_fee:.2f}</td>
                                    </tr>''' if platform_fee > 0 else ''}
                                    <tr>
                                        <td style="padding: 5px 0; color: #666666; font-size: 14px;">Tax:</td>
                                        <td style="padding: 5px 0; color: #111111; font-size: 14px; text-align: right;">₹{tax:.2f}</td>
                                    </tr>
                                    <tr style="border-top: 2px solid #e0e0e0;">
                                        <td style="padding: 15px 0 5px 0; color: #111111; font-size: 18px; font-weight: bold;">Total:</td>
                                        <td style="padding: 15px 0 5px 0; color: #c7511f; font-size: 18px; font-weight: bold; text-align: right;">
                                            ₹{total:.2f}
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Shipping Address -->
                        <tr>
                            <td style="padding: 0 30px 30px 30px;">
                                <div style="background-color: #f3f3f3; padding: 20px; border-radius: 4px;">
                                    <h3 style="margin: 0 0 10px 0; color: #111111; font-size: 16px; font-weight: bold;">Shipping Address:</h3>
                                    <p style="margin: 0; color: #333333; font-size: 14px; line-height: 1.6;">
                                        {shipping_address}
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Customer Information -->
                        <tr>
                            <td style="padding: 0 30px 30px 30px;">
                                <div style="background-color: #f3f3f3; padding: 20px; border-radius: 4px;">
                                    <h3 style="margin: 0 0 10px 0; color: #111111; font-size: 16px; font-weight: bold;">Customer:</h3>
                                    <p style="margin: 0 0 5px 0; color: #333333; font-size: 14px;">
                                        <strong>Name:</strong> {user.get_full_name() or user.email}
                                    </p>
                                    <p style="margin: 0 0 5px 0; color: #333333; font-size: 14px;">
                                        <strong>Email:</strong> {user.email}
                                    </p>
                                    {f'''<p style="margin: 0; color: #333333; font-size: 14px;">
                                        <strong>Phone:</strong> {user.phone_number}
                                    </p>''' if hasattr(user, 'phone_number') and user.phone_number else ''}
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px; background-color: #232f3e; text-align: center;">
                                <p style="margin: 0 0 10px 0; color: #ffffff; font-size: 14px;">
                                    If you have any questions, visit <a href="https://sixpine.in" style="color: #ff9900; text-decoration: none;">Seller Central</a>
                                </p>
                                <p style="margin: 0 0 15px 0; color: #cccccc; font-size: 12px;">
                                    To change your email preferences, visit <a href="https://sixpine.in/settings" style="color: #ff9900; text-decoration: none;">Notification Preferences</a>
                                </p>
                                <p style="margin: 0; color: #999999; font-size: 11px; line-height: 1.5;">
                                    We hope you found this message to be useful. However, if you'd rather not receive future e-mails of this sort from Sixpine, 
                                    <a href="https://sixpine.in/unsubscribe" style="color: #ff9900; text-decoration: none;">click out here</a>.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    return html_content


def send_order_confirmation_to_admin(order):
    """
    Send order confirmation email to admin
    
    Args:
        order: Order instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get admin notification email from settings
        admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', '')
        
        if not admin_email:
            logger.warning('ADMIN_NOTIFICATION_EMAIL not configured in settings')
            return False
        
        # Get user details
        user = order.user
        
        # Generate email content
        html_content = get_order_confirmation_email_html(order, user)
        
        # Plain text fallback
        plain_text = f"""
New Order Notification - Sixpine

Order Date: {order.created_at.strftime('%d/%m/%Y')}
Customer: {user.get_full_name() or user.email}
Payment Method: {dict(order.PAYMENT_METHOD_CHOICES).get(order.payment_method, order.payment_method)}
Total Amount: ₹{order.total_amount:.2f}

Please login to the admin panel to view full order details.
        """
        
        # Send email using Brevo service
        email_service = BrevoEmailService()
        subject = 'New Order Received - Sixpine'
        
        success = email_service.send_email(
            to_email=admin_email,
            subject=subject,
            body=plain_text,
            html_content=html_content
        )
        
        if success:
            logger.info(f'Order confirmation email sent to admin for order {order.order_id}')
        else:
            logger.error(f'Failed to send order confirmation email to admin for order {order.order_id}')
            if hasattr(email_service, 'last_error') and email_service.last_error:
                logger.error(f'Error details: {email_service.last_error}')
        
        return success
        
    except Exception as e:
        logger.error(f'Error sending order confirmation email: {str(e)}', exc_info=True)
        return False
