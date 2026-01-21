from django.urls import path
from . import views
from . import return_views

urlpatterns = [
    path('addresses/', views.AddressListCreateView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/<uuid:order_id>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<uuid:order_id>/invoice/', views.download_invoice, name='download-invoice'),
    path('orders/create/', views.OrderCreateView.as_view(), name='order-create'),
    path('orders/checkout/', views.checkout_from_cart, name='checkout-from-cart'),
    path('orders/<uuid:order_id>/cancel/', views.cancel_order, name='cancel-order'),
    path('orders/razorpay/create-order/', views.create_razorpay_order, name='create-razorpay-order'),
    path('orders/razorpay/verify-payment/', views.verify_razorpay_payment, name='verify-razorpay-payment'),
    path('orders/cashfree/create-order/', views.create_cashfree_order, name='create-cashfree-order'),
    path('orders/cashfree/verify-payment/', views.verify_cashfree_payment, name='verify-cashfree-payment'),
    path('orders/checkout/cod/', views.checkout_with_cod, name='checkout-cod'),
    path('orders/complete-payment/', views.complete_payment, name='complete-payment'),
    path('razorpay-key/', views.get_razorpay_key, name='get-razorpay-key'),
    path('cashfree-app-id/', views.get_cashfree_app_id, name='get-cashfree-app-id'),
    path('payment-charges/', views.get_payment_charges, name='get-payment-charges'),
    path('payment-gateway/', views.get_active_payment_gateway, name='get-active-payment-gateway'),
    path('orders/validate-coupon/', views.validate_coupon, name='validate-coupon'),
    path('coupons/validate/', views.validate_coupon, name='validate-coupon-alt'),  # Alternative path for backward compatibility
    path('returns/submit/', return_views.submit_return_request, name='submit-return-request'),
    path('returns/', return_views.get_return_requests, name='get-return-requests'),
    path('returns/seller/', return_views.get_seller_return_requests, name='get-seller-return-requests'),
    path('returns/<int:return_request_id>/approve/', return_views.approve_return_request, name='approve-return-request'),
    path('returns/admin/sixpine/', return_views.get_admin_sixpine_return_requests, name='get-admin-sixpine-return-requests'),
    path('returns/admin/sixpine/<int:return_request_id>/approve/', return_views.approve_admin_sixpine_return_request, name='approve-admin-sixpine-return-request'),
]