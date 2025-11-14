from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product


class CartView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_to_cart(request):
    """Add item to cart or update quantity if item exists"""
    from products.models import ProductVariant
    
    product_id = request.data.get('product_id')
    variant_id = request.data.get('variant_id')
    quantity = int(request.data.get('quantity', 1))
    
    if not product_id:
        return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if product has variants - variant_id is required if variants exist
    has_variants = product.variants.exists()
    variant = None
    
    if has_variants:
        if not variant_id:
            return Response({
                'error': 'Variant is required for this product. Please select a color, size, or pattern.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
        except ProductVariant.DoesNotExist:
            return Response({'error': 'Invalid variant selected'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Stock check for variant
        if quantity > variant.stock_quantity:
            return Response({
                'error': f'Only {variant.stock_quantity} items available in stock for this variant'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, 
        product=product,
        variant=variant,
        defaults={'quantity': quantity}
    )
    
    if not created:
        # Update existing item quantity
        new_quantity = cart_item.quantity + quantity
        
        # Stock check for variants
        if variant:
            if new_quantity > variant.stock_quantity:
                return Response({
                    'error': f'Cannot add {quantity} more items. Only {variant.stock_quantity - cart_item.quantity} more available'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item.quantity = new_quantity
        cart_item.save()
    
    return Response({
        'message': 'Item added to cart successfully',
        'cart': CartSerializer(cart, context={'request': request}).data
    })


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    quantity = int(request.data.get('quantity', 1))
    
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if quantity <= 0:
        cart_item.delete()
        return Response({'message': 'Item removed from cart'})
    
    # Check variant stock if variant exists
    if cart_item.variant:
        if quantity > cart_item.variant.stock_quantity:
            return Response({
                'error': f'Only {cart_item.variant.stock_quantity} items available in stock for this variant'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    cart_item.quantity = quantity
    cart_item.save()
    
    return Response({
        'message': 'Cart updated successfully',
        'cart': CartSerializer(cart_item.cart, context={'request': request}).data
    })


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    
    return Response({'message': 'Item removed from cart successfully'})


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def clear_cart(request):
    """Clear all items from cart"""
    cart = get_object_or_404(Cart, user=request.user)
    cart.items.all().delete()
    
    return Response({'message': 'Cart cleared successfully'})
