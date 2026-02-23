from django.shortcuts import render
from .models import Product, Category, Variant
from django.contrib.auth.models import User

# Create your views here.
def welcome(request):
    return render(request, 'welcome.html')

def home(request):
    products = Product.objects.filter(is_available=True).order_by('sort_order')
    categories = Category.objects.filter(is_active=True).order_by('sort_order')
    show_all = request.GET.get("all")

    if show_all != 'true':
        products = products[:8]

    context = {
        'signUp': True,
        'search_bar': True,
        'products': products,
        'categories': categories,
        'show_all': show_all == 'true'
    }
    return render(request, 'home/homepage.html', context)

def getbyCategory(request, category_id):
    category = Category.objects.get(id=category_id)
    products = Product.objects.filter(category=category, is_available=True).order_by('sort_order')
    categories = Category.objects.filter(is_active=True).order_by('sort_order')
    context = {
        'signUp': True,
        'search_bar': True,
        'products': products,
        'categories': categories,
    }
    return render(request, 'home/homepage.html', context)

