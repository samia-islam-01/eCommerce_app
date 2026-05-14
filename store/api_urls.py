from django.urls import path
from . import api_views

urlpatterns = [
    # Products
    path('products/', api_views.ProductListCreateView.as_view(), name='api_products'),
    path('products/mine/', api_views.MyProductsView.as_view(), name='api_my_products'),
    path('products/<int:product_id>/', api_views.ProductDetailView.as_view(), name='api_product_detail'),
    path('products/<int:product_id>/reviews/', api_views.ReviewCreateView.as_view(), name='api_add_review'),

    # Stores
    path('stores/', api_views.StoreListCreateView.as_view(), name='api_stores'),
    path('stores/<int:store_id>/', api_views.StoreDetailView.as_view(), name='api_store_detail'),

    # Cart & Checkout
    path('cart/', api_views.CartView.as_view(), name='api_cart'),
    path('checkout/', api_views.CheckoutView.as_view(), name='api_checkout'),
    path('stores/<int:store_id>/products/', api_views.StoreProductsView.as_view(), name='api_store_products'),
]