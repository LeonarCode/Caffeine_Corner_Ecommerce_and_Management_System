from django.shortcuts import render
from .models import Product, Category, Variant

# Create your views here.
def welcome(request):
    return render(request, 'welcome.html')

def home(request):
    context = {
        'signUp': True,
        'search_bar': True,
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
