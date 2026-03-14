from django.urls import path
from . import views


urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('home/', views.home, name='home'),
    path('cart/<int:user_id>/', views.cart, name='cart'),
    path('category/<int:category_id>/', views.getbyCategory, name='getbyCategory'),
    path('all-products/', views.getAllProducts, name='getAllProducts'),
    path('product/<int:product_id>/', views.buyProduct, name='buyProduct'),
    path('cart/add/<int:product_id>/', views.addToCart, name='addToCart'),
    path('cart/remove/<int:cart_item_id>/', views.removeFromCart, name='removeFromCart'),
    path('cart/clear/', views.clearCart, name='clearCart'),
    path('search/', views.search, name='search'),
]