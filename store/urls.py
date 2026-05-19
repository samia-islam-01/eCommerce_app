from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Home page: Shows the list of all products
    path('login/', views.list_products, name='products_list'),

    # Page to view details about a specific product (with a search form)
    path('product/', views.view_product_page, name='product_page'),

    # Page to change the price of a product (for users with permission)
    path('change-price/', views.change_product_price, name='change_price'),

    # URL to add an item to the shopping cart (usually called by a form)
    path('add-to-cart/', views.add_item_to_cart, name='add_to_cart'),

    # Page showing all items currently in the user's cart with totals
    path('cart/', views.show_user_cart, name='main_cart_page'),

    # URL to clear all items from the user's cart
    path('clear-cart/', views.clear_cart, name='clear_cart'),

    path('checkout/', views.checkout, name='checkout'),

    path('create/', views.create_product, name='create_product'),

    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    path('product/<int:product_id>/review/', views.add_review, name='add_review'),

    path('edit/<int:product_id>/', views.edit_product, name='edit_product'),

    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),

    path('stores/', views.my_stores, name='my_stores'),

    path('stores/create/', views.create_store, name='create_store'),

    path('stores/edit/<int:store_id>/', views.edit_store, name='edit_store'),

    path('stores/delete/<int:store_id>/', views.delete_store, name='delete_store'),

    path('my-products/', views.my_products, name='my_products'),
]
