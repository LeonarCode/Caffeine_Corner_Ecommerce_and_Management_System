from django.shortcuts import render
from .models import Product, Category, Variant

# Create your views here.
def welcome(request):
    return render(request, 'welcome.html')

def home(request):
    return render(request, 'home/homepage.html')

def signin(request):
    return render(request, 'authentication/signin.html')

def signup(request):
    return render(request, 'authentication/signup.html')
