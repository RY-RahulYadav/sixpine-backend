from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ['product', 'quantity', 'total_price']
    readonly_fields = ['total_price']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'items_count', 'total_items', 'total_price', 'updated_at']
    search_fields = ['user__username']
    readonly_fields = ['items_count', 'total_items', 'total_price', 'created_at', 'updated_at']
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'total_price', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['cart__user__username', 'product__title']
    readonly_fields = ['total_price']
