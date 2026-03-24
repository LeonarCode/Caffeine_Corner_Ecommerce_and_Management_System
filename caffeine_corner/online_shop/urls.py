from django.urls import path
from . import views


urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('home/', views.home, name='home'),
    path('cart/<int:user_id>/', views.cart, name='cart'),
    path('category/<int:category_id>/', views.getbyCategory, name='getbyCategory'),
    path('all-products/', views.getAllProducts, name='getAllProducts'),
    path('cart/add/<int:product_id>/', views.addToCart, name='addToCart'),
    path('cart/remove/<int:cart_item_id>/', views.removeFromCart, name='removeFromCart'),
    path('cart/update/<int:cart_item_id>/', views.updateCartItem, name='updateCartItem'),
    path('search/', views.search, name='search'),
    path('checkout/<int:product_id>', views.checkout, name='checkout'),
    path('cart-checkout/', views.cartCheckout, name='cartCheckout'),
    path('webhooks/paymongo/', views.paymongo_webhook, name='paymongo_webhook'),
    path('order/', views.placeOrder, name='placeOrder'),
    path('order/success/', views.orderSuccess, name='orderSuccess'),
    path('order/failed/',  views.orderFailed,  name='orderFailed'),
    path('order/place-from-cart/', views.placeOrderFromCart, name='placeOrderFromCart'),
]