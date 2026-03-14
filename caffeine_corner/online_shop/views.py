from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Variant, Rating, Order, CartItem
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
# Create your views here.

def welcome(request):
    return render(request, 'welcome.html')


def home(request):
    products = Product.objects.filter(is_available=True).order_by('sort_order')
    categories = Category.objects.filter(is_active=True).order_by('sort_order')
    ratings = Rating.objects.select_related('product').all()
    user = request.user if request.user.is_authenticated else None
    show_all = request.GET.get("all")

    if show_all != 'true':
        products = products[:8]

    context = {
        'show_footer': True,
        'signUp': True,
        'search_bar': True,
        'products': products,
        'categories': categories,
        'user': user,
        'show_all': show_all == 'true'
    }
    return render(request, 'home/homepage.html', context)

def cart(request, user_id):
    user = User.objects.get(id=user_id)
    cart_items = CartItem.objects.filter(user=user)
    total = sum(item.subtotal for item in cart_items)
    context = {
        'show_footer': True,
        'signUp': True,
        'search_bar': True,
        'cart_items': cart_items,
        'total': total,
        'user': user,
    }
    if not request.user.is_authenticated:
        return redirect('signin')
    return render(request, 'home/cart.html', context)

def getbyCategory(request, category_id):
    category = Category.objects.get(id=category_id)
    products = Product.objects.filter(category=category, is_available=True).order_by('sort_order')

    data = {
        'products': [
            {
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'price': str(p.price),
                'average_rating': p.average_rating,
                'image': request.build_absolute_uri(p.image.url),
            }
            for p in products
        ]
    }
    return JsonResponse(data)

def getAllProducts(request):
    products = Product.objects.filter(is_available=True).order_by('sort_order')

    data = {
        'products': [
            {
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'price': str(p.price),
                'average_rating': p.average_rating,
                'image': request.build_absolute_uri(p.image.url),
            }
            for p in products
        ]
    }
    return JsonResponse(data)
    
def search(request):
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'products': []})
    
    products = Product.objects.filter(
        is_available=True
    ).filter(
        models.Q(name__icontains=query) |
        models.Q(description__icontains=query) |
        models.Q(category__name__icontains=query)
    ).select_related('category')[:8]  # limit to 8 results

    return JsonResponse({
        'products': [
            {
                'id': p.id,
                'name': p.name,
                'price': str(p.price),
                'image': request.build_absolute_uri(p.image.url),
                'category': p.category.name if p.category else '',
                'query': query,
            }
            for p in products
        ]
    })    

def buyProduct(request, product_id):
    product = Product.objects.get(id=product_id)
    data = {
        'name': product.name,
        'price': product.price,
        'image': product.image.url,
        'description': product.description,
        'rating': product.average_rating,
    }
    return JsonResponse(data)

# views.py
@require_POST
def addToCart(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)

    product = get_object_or_404(Product, id=product_id)

    cart_item = CartItem.objects.filter(
        user=request.user,
        product=product,
        variant__isnull=True
    ).first()

    if cart_item:
        cart_item.quantity += 1
        cart_item.save()
    else:
        cart_item = CartItem.objects.create(
            user=request.user,
            product=product,
            variant=None,
            quantity=1
        )

    cart_total = CartItem.objects.filter(user=request.user).count()

    return JsonResponse({
        'success': True,
        'quantity': cart_item.quantity,
        'cart_total': cart_total
    })

def removeFromCart(request, cart_item_id):
    cart_item = CartItem.objects.get(id=cart_item_id)
    cart_item.quantity -= 1
    if cart_item.quantity == 0:
        cart_item.delete()
    else:
        cart_item.save()
    return JsonResponse({'success': True, 'cart_item': cart_item.id})

def clearCart(request):
    CartItem.objects.filter(user=request.user).delete()
    return JsonResponse({'success': True})