from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Registration with OTP
    path('register/request-otp/', views.request_otp_view, name='request_otp'),
    path('register/verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('register/resend-otp/', views.resend_otp_view, name='resend_otp'),
    
    # Password reset
    path('password-reset/request/', views.password_reset_request_view, name='password_reset_request'),
    path('password-reset/confirm/', views.password_reset_confirm_view, name='password_reset_confirm'),
    
    # Profile management
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile_view, name='update_profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    
    # Contact form
    path('contact/submit/', views.contact_form_submit, name='contact_submit'),
    
    # Bulk orders
    path('bulk-order/submit/', views.bulk_order_submit, name='bulk_order_submit'),
    
    path('payment-preferences/', views.get_payment_preference, name='get_payment_preference'),
    path('payment-preferences/update/', views.update_payment_preference, name='update_payment_preference'),
    path('payment-preferences/saved-cards/', views.get_saved_cards, name='get_saved_cards'),
    path('payment-preferences/saved-cards/<str:token_id>/delete/', views.delete_saved_card, name='delete_saved_card'),
    
    # Data requests
    path('data-requests/create/', views.create_data_request, name='create_data_request'),
    path('data-requests/', views.get_user_data_requests, name='get_user_data_requests'),
    path('data-requests/<int:request_id>/download/', views.download_data_file, name='download_data_file'),
    
    # Account closure
    path('account/check-deletion-eligibility/', views.check_account_deletion_eligibility, name='check_account_deletion_eligibility'),
    path('account/close/', views.close_account, name='close_account'),
    
    # Vendor authentication
    path('vendor/register/', views.vendor_register_view, name='vendor_register'),
    path('vendor/login/', views.vendor_login_view, name='vendor_login'),
    path('vendor/profile/', views.vendor_profile_view, name='vendor_profile'),
]
