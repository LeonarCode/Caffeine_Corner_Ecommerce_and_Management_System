from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Variant, Rating, Order, CartItem
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import requests
import base64
import os
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

def create_paymongo_source(amount_cents, success_url, failed_url):
    secret_key = os.getenv("PAYMONGO_SKEY")
    encoded    = base64.b64encode(f"{secret_key}:".encode()).decode()
    res = requests.post(
        "https://api.paymongo.com/v1/sources",
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type":  "application/json"
        },
        json={
            "data": {
                "attributes": {
                    "amount":   amount_cents,
                    "currency": "PHP",
                    "type":     "gcash",
                    "redirect": {
                        "success": success_url,
                        "failed":  failed_url
                    }
                }
            }
        }
    )
    return res.json()

def checkout(request, product_id):
    product  = get_object_or_404(Product, id=product_id)
    variants = product.variants.all()  # get all sizes
    error    = request.GET.get('error')
    error_message = 'Payment setup failed. Please try again.' if error == 'payment_failed' else None
    return render(request, 'home/checkout.html', {
        'product':       product,
        'variants':      variants,
        'error_message': error_message,
    })

def placeOrder(request):
    if request.method != 'POST':
        return redirect('home')

    product_id = request.POST.get('product_id')
    variant_id = request.POST.get('variant_id')  # ← new
    quantity   = int(request.POST.get('quantity', 1))
    email      = request.POST.get('email')
    address    = request.POST.get('address')
    notes      = request.POST.get('notes', '')
    payment_method = request.POST.get('payment_method', 'cod')
    gcash_ref      = request.POST.get('gcash_ref', '')

    product = get_object_or_404(Product, id=product_id, is_available=True)
    user    = request.user if request.user.is_authenticated else None

    # Get variant if selected
    variant = None
    if variant_id:
        variant = get_object_or_404(Variant, id=variant_id, product=product)

    # Calculate total price with variant additional price
    unit_price   = product.price + (variant.additional_price if variant else 0)
    amount_cents = int(unit_price * quantity * 100)

    if payment_method == 'gcash':
        order = Order.objects.create(
            user=user, email=email, address=address, notes=notes,
            product=product, variant=variant, quantity=quantity,
            payment_method='gcash', payment_status='unpaid',
            gcash_ref=gcash_ref,
        )
        try:
            success_url  = request.build_absolute_uri(f'/order/success/?order_id={order.id}')
            failed_url   = request.build_absolute_uri(f'/order/failed/?order_id={order.id}')
            data         = create_paymongo_source(amount_cents, success_url, failed_url)
            source       = data['data']
            checkout_url = source['attributes']['redirect']['checkout_url']
            order.paymongo_id = source['id']
            order.save()
            return redirect(checkout_url)
        except Exception as e:
            order.delete()
            return redirect(f'/checkout/{product_id}/?error=payment_failed')
    else:
        Order.objects.create(
            user=user, email=email, address=address, notes=notes,
            product=product, variant=variant, quantity=quantity,
            payment_method='cod', payment_status='unpaid',
        )
        return redirect('/?order=success')
    
def orderSuccess(request):
    order_id = request.GET.get('order_id')
    if order_id:
        order = Order.objects.filter(id=order_id).first()
        if order:
            order.payment_status = 'paid'
            order.status         = 'confirmed'
            order.save()
    # Render home with success flag — JS will show the overlay
    return redirect('/?order=success')


def orderFailed(request):
    order_id = request.GET.get('order_id')
    if order_id:
        order = Order.objects.filter(id=order_id).first()
        if order:
            order.payment_status = 'failed'
            order.status         = 'cancelled'
            order.save()
    return redirect('/?order=failed')

