from django.contrib import admin
from .models import Address, Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['product', 'quantity', 'price', 'total_price']
    readonly_fields = ['total_price']


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    fields = ['status', 'notes', 'created_at', 'created_by']
    readonly_fields = ['created_at']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'type', 'city', 'state', 'is_default', 'created_at']
    list_filter = ['type', 'is_default', 'state', 'created_at']
    search_fields = ['user__username', 'full_name', 'city', 'phone']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'status', 'payment_status', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_id', 'user__username', 'tracking_number']
    readonly_fields = ['order_id', 'items_count', 'created_at', 'updated_at']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'user', 'status', 'payment_status')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'total_amount')
        }),
        ('Shipping', {
            'fields': ('shipping_address', 'tracking_number', 'estimated_delivery', 'delivered_at')
        }),
        ('Notes', {
            'fields': ('order_notes',)
        }),
        ('Metadata', {
            'fields': ('items_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'total_price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['order__order_id', 'product__title']
    readonly_fields = ['total_price']


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'created_at', 'created_by']
    list_filter = ['status', 'created_at']
    search_fields = ['order__order_id', 'notes']
