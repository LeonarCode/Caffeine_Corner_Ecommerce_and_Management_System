from django.urls import path
from . import views


urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('home/', views.home, name='home'),
    path('category/<int:category_id>/', views.getbyCategory, name='getbyCategory'),
]