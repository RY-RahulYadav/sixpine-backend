from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    seller_dashboard_stats, seller_brand_analytics, seller_shipment_settings,
    seller_settings, seller_change_password,
    SellerProductViewSet, SellerOrderViewSet,
    SellerCouponViewSet, SellerMediaViewSet,
    vendor_review_list, vendor_review_approve, vendor_review_reject
)
from .communication import get_customers_list, get_admin_email, seller_send_email
from .payment import seller_payment_dashboard

router = DefaultRouter()
router.register(r'products', SellerProductViewSet, basename='seller-products')
router.register(r'orders', SellerOrderViewSet, basename='seller-orders')
router.register(r'coupons', SellerCouponViewSet, basename='seller-coupons')
router.register(r'media', SellerMediaViewSet, basename='seller-media')

urlpatterns = [
    path('dashboard/stats/', seller_dashboard_stats, name='seller-dashboard-stats'),
    path('brand-analytics/', seller_brand_analytics, name='seller-brand-analytics'),
    path('shipment-settings/', seller_shipment_settings, name='seller-shipment-settings'),
    path('settings/', seller_settings, name='seller-settings'),
    path('settings/change-password/', seller_change_password, name='seller-change-password'),
    path('communication/customers/', get_customers_list, name='seller-customers-list'),
    path('communication/admin-email/', get_admin_email, name='seller-admin-email'),
    path('communication/send-email/', seller_send_email, name='seller-send-email'),
    path('payment/dashboard/', seller_payment_dashboard, name='seller-payment-dashboard'),
    path('reviews/', vendor_review_list, name='vendor-review-list'),
    path('reviews/<int:review_id>/approve/', vendor_review_approve, name='vendor-review-approve'),
    path('reviews/<int:review_id>/reject/', vendor_review_reject, name='vendor-review-reject'),
    path('', include(router.urls)),
]

