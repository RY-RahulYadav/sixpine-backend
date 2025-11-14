from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Product listing and detail
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Search
    path('products/search/', views.ProductSearchView.as_view(), name='product-search'),
    path('products/advanced-search/', views.ProductListView.as_view(), name='advanced-search'),
    path('search/suggestions/', views.get_search_suggestions, name='search-suggestions'),
    
    # Categories and filters
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:category_slug>/subcategories/', views.SubcategoryListView.as_view(), name='subcategory-list'),
    path('colors/', views.ColorListView.as_view(), name='color-list'),
    path('materials/', views.MaterialListView.as_view(), name='material-list'),
    path('filter-options/', views.get_filter_options, name='filter-options'),
    path('brands/', views.get_brands, name='brands-list'),
    
    # Special product lists
    path('products/featured/', views.get_featured_products, name='featured-products'),
    path('products/new-arrivals/', views.get_new_arrivals, name='new-arrivals'),
    path('home-data/', views.get_home_data, name='home-data'),
    path('homepage-content/', views.get_homepage_content, name='homepage-content'),
    path('bulk-order-page-content/', views.get_bulk_order_page_content, name='bulk-order-page-content'),
    
    # Product reviews
    path('products/<slug:slug>/reviews/', views.ProductReviewListView.as_view(), name='product-reviews'),
    
    # Product recommendations
    path('products/<slug:slug>/recommendations/', views.get_product_recommendations, name='product-recommendations'),
    
    # Product offers
    path('offers/', views.get_active_offers, name='active-offers'),
    path('offers/create/', views.create_offer, name='create-offer'),
    
    path('browsing-history/track/', views.track_browsing_history, name='track-browsing-history'),
    path('browsing-history/categories/', views.get_browsed_categories, name='browsed-categories'),
    path('browsing-history/clear/', views.clear_browsing_history, name='clear-browsing-history'),
    path('browsing-history/', views.get_browsing_history, name='browsing-history'),
]