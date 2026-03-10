from django.urls import path
from . import views


urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('home/', views.home, name='home'),
    path('category/<int:category_id>/', views.getbyCategory, name='getbyCategory'),
    path('product/<int:product_id>/', views.buyProduct, name='buyProduct'),
]