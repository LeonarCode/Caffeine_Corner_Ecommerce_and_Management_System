from django.shortcuts import render
from .models import Product, Category, Variant

# Create your views here.
def welcome(request):
    return render(request, 'welcome.html')
