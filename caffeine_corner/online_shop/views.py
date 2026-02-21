from django.shortcuts import render
from .models import Product, Category, Variant, UserProfile
from django.contrib.auth.models import User

# Create your views here.
def welcome(request):
    return render(request, 'welcome.html')

def home(request):
    products = Product.objects.filter(is_available=True).order_by('sort_order')
    categories = Category.objects.filter(is_active=True).order_by('sort_order')
    context = {
        'signUp': True,
        'search_bar': True,
        'products': products,
        'categories': categories,
    }
    return render(request, 'home/homepage.html', context)

def signin(request):
    return render(request, 'authentication/signin.html')

def signup(request):
    return render(request, 'authentication/signup.html')

def email_signup(request):
    return render(request, 'authentication/emailSignup.html')

def email_signin(request):
    return render(request, 'authentication/emailSignin.html')
