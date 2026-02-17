from django.urls import path
from . import views


urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('home/', views.home, name='home'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('email-signup/', views.email_signup, name='email_signup'),
    path('email-signin/', views.email_signin, name='email_signin'),
]