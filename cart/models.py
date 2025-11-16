from django.db import models
from django.conf import settings
from products.models import Product, ProductVariant
from django.core.validators import MinValueValidator
from decimal import Decimal


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def items_count(self):
        return self.items.count()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product', 'variant']

    def __str__(self):
        variant_info = f" - {self.variant}" if self.variant else ""
        return f"{self.quantity} x {self.product.title}{variant_info} in {self.cart.user.username}'s cart"

    @property
    def total_price(self):
        # Use variant price if available, otherwise get from first active variant
        if self.variant and self.variant.price:
            price = self.variant.price
        else:
            # Fallback: get price from first active variant
            first_variant = self.product.variants.filter(is_active=True).first()
            if first_variant and first_variant.price:
                price = first_variant.price
            else:
                # If no variant found, return 0 (shouldn't happen in normal flow)
                return Decimal('0.00')
        return self.quantity * price

    def save(self, *args, **kwargs):
        # If product has variants, variant must be specified
        if self.product.variants.exists() and not self.variant:
            raise ValueError("Variant must be specified for products with variants")
        
        # Check variant stock
        if self.variant:
            if self.quantity > self.variant.stock_quantity:
                raise ValueError(f"Only {self.variant.stock_quantity} items available in stock for this variant")
        
        super().save(*args, **kwargs)
