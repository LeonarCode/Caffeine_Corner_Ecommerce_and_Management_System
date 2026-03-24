from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from .models import LoyaltyPoint, Product, Category, Variant, Rating, Order, CartItem, OrderItem
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import requests
import base64
import os
import hmac
import hashlib
import json
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
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    try:
        cart_item = CartItem.objects.get(id=cart_item_id, user=request.user)
        cart_item.delete()
        
        remaining   = CartItem.objects.filter(user=request.user).select_related('product', 'variant')
        cart_total  = sum(
            (item.product.price + (item.variant.additional_price if item.variant else 0)) * item.quantity
            for item in remaining
        )
        
        return JsonResponse({
            'success':    True,
            'cart_total': float(cart_total),
            'cart_count': remaining.count()
        })
    except CartItem.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)


def updateCartItem(request, cart_item_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    try:
        import json
        body     = json.loads(request.body)
        quantity = int(body.get('quantity', 1))
        
        if quantity < 1:
            return JsonResponse({'error': 'Quantity must be at least 1'}, status=400)
        if quantity > 9999:
            return JsonResponse({'error': 'Quantity cannot exceed 9999'}, status=400)

        cart_item          = CartItem.objects.get(id=cart_item_id, user=request.user)
        cart_item.quantity = quantity
        cart_item.save()

        unit_price   = cart_item.product.price + (cart_item.variant.additional_price if cart_item.variant else 0)
        item_subtotal = float(unit_price * quantity)

        remaining  = CartItem.objects.filter(user=request.user).select_related('product', 'variant')
        cart_total = sum(
            (item.product.price + (item.variant.additional_price if item.variant else 0)) * item.quantity
            for item in remaining
        )

        return JsonResponse({
            'success':      True,
            'quantity':     quantity,
            'subtotal':     item_subtotal,
            'cart_total':   float(cart_total),
            'cart_count':   remaining.count()
        })
    except CartItem.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)
    except (ValueError, KeyError):
        return JsonResponse({'error': 'Invalid quantity'}, status=400)

@csrf_exempt  # PayMongo ang nagse-send, hindi ang iyong form
def paymongo_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    # 1. I-verify na galing talaga ito sa PayMongo
    webhook_secret = os.getenv("PAYMONGO_WEBHOOK_SECRET")
    sig_header     = request.headers.get("Paymongo-Signature", "")
    
    # I-parse ang signature header: t=timestamp,te=sig,li=sig
    sig_parts = {}
    for part in sig_header.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            sig_parts[k.strip()] = v.strip()

    timestamp  = sig_parts.get("t", "")
    test_sig   = sig_parts.get("te", "")  # test mode
    live_sig   = sig_parts.get("li", "")  # live mode

    raw_body = request.body.decode("utf-8")
    message  = f"{timestamp}.{raw_body}"
    expected = hmac.new(
        webhook_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    # Tanggapin ang test o live signature
    if expected not in (test_sig, live_sig):
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # 2. I-process ang event
    payload    = json.loads(raw_body)
    event_type = payload.get("data", {}).get("attributes", {}).get("type", "")

    if event_type == "source.chargeable":
        source_data = payload["data"]["attributes"]["data"]
        source_id   = source_data["id"]
        amount      = source_data["attributes"]["amount"]

        # Hanapin ang order gamit ang paymongo_id
        order = Order.objects.filter(paymongo_id=source_id).first()
        if not order:
            JsonResponse({'error': 'Order not found'}, status=404)

        # 3. I-create ang Payment
        _create_paymongo_payment(source_id, amount, order)

    elif event_type == "payment.paid":
        payment_data = payload["data"]["attributes"]["data"]
        source_id    = payment_data["attributes"].get("source", {}).get("id", "")

        order = Order.objects.filter(paymongo_id=source_id).first()
        if order:
            order.payment_status = "paid"
            order.status         = "confirmed"
            order.save()

            # 4. I-clear na ang cart dito — SECURE na!
            if order.user:
                CartItem.objects.filter(user=order.user).delete()
                _award_loyalty_points(order.user, order.total_price)

    return JsonResponse({'status': 'ok'}, status=200)


def _get_paymongo_headers():
    """Shared helper para sa PayMongo API headers."""
    secret_key = os.getenv("PAYMONGO_SKEY")
    encoded    = base64.b64encode(f"{secret_key}:".encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type":  "application/json",
    }

def create_paymongo_source(amount_cents, success_url, failed_url):
    res = requests.post(
        "https://api.paymongo.com/v1/sources",
        headers=_get_paymongo_headers(),
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

def _create_paymongo_payment(source_id, amount, order):
    try:
        requests.post(
            "https://api.paymongo.com/v1/payments",
            headers=_get_paymongo_headers(),
            json={
                "data": {
                    "attributes": {
                        "amount":      amount,
                        "currency":    "PHP",
                        "source":      {"id": source_id, "type": "source"},
                        "description": f"Caffeine Corner Order #{order.id}",
                    }
                }
            },
        )
    except Exception as e:
        print(f"PayMongo payment creation failed: {e}")

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

def cartCheckout(request):
    if not request.user.is_authenticated:
        return redirect('signin')

    user       = request.user
    cart_items = CartItem.objects.filter(user=user).select_related('product', 'variant')

    if not cart_items.exists():
        return redirect('cart', user_id=user.id)

    # Calculate total
    total = sum(
        (item.product.price + (item.variant.additional_price if item.variant else 0)) * item.quantity
        for item in cart_items
    )
    error = request.GET.get('error')

    return render(request, 'home/cart_checkout.html', {
        'cart_items':    cart_items,
        'cart_total':    total,
        'error_message': 'Payment setup failed. Please try again.' if error else None,
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
    points_to_use = int(request.POST.get('points_to_use', 0))
    discount = 0

    loyalty = None
    if user and points_to_use > 0:
        try:
            loyalty  = LoyaltyPoint.objects.get(user=user)
            discount = loyalty.redeem(points_to_use)
            total   -= discount  # i-apply ang discount sa total
            if total < 0:
                total = 0
        except (LoyaltyPoint.DoesNotExist, ValueError):
            points_to_use = 0
            discount      = 0

    amount_cents = int(total * 100)
    # Get variant if selected
    variant = None
    if variant_id:
        variant = get_object_or_404(Variant, id=variant_id, product=product)

    # Calculate total price with variant additional price
    unit_price   = product.price + (variant.additional_price if variant else 0)
    amount_cents = int(unit_price * quantity * 100)
    if payment_method == 'cod':
        _award_loyalty_points(user, total)
    if payment_method == 'gcash':
        order = Order.objects.create(
            user=user, email=email, address=address, notes=notes,
            product=product, variant=variant, quantity=quantity,
            payment_method='gcash', payment_status='unpaid',
            gcash_ref=gcash_ref, discount = discount,
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
    
def placeOrderFromCart(request):
    if request.method != 'POST':
        return redirect('home')

    email          = request.POST.get('email')
    address        = request.POST.get('address')
    notes          = request.POST.get('notes', '')
    payment_method = request.POST.get('payment_method', 'cod')
    gcash_ref      = request.POST.get('gcash_ref', '')
    user           = request.user if request.user.is_authenticated else None
    points_to_use = int(request.POST.get('points_to_use', 0))
    discount = 0

    loyalty = None
    if user and points_to_use > 0:
        try:
            loyalty  = LoyaltyPoint.objects.get(user=user)
            discount = loyalty.redeem(points_to_use)
            total   -= discount  # i-apply ang discount sa total
            if total < 0:
                total = 0
        except (LoyaltyPoint.DoesNotExist, ValueError):
            points_to_use = 0
            discount      = 0

    amount_cents = int(total * 100)
    # Get cart items
    if not user:
        return redirect('signin')  # cart requires login
    cart_items = CartItem.objects.filter(user=user).select_related('product', 'variant')

    if not cart_items.exists():
        return redirect('cart', user_id=user.id)

    # Calculate total
    total = sum(
        (item.product.price + (item.variant.additional_price if item.variant else 0)) * item.quantity
        for item in cart_items
    )
    amount_cents = int(total * 100)

    # Create Order
    order = Order.objects.create(
        user           = user,
        email          = email,
        address        = address,
        notes          = notes,
        payment_method = payment_method,
        payment_status = 'unpaid',
        gcash_ref      = gcash_ref,
        discount = discount
    )

    # Create OrderItems from cart
    for item in cart_items:
        unit_price = item.product.price + (item.variant.additional_price if item.variant else 0)
        OrderItem.objects.create(
            order    = order,
            product  = item.product,
            variant  = item.variant,
            quantity = item.quantity,
            price    = unit_price,  # snapshot price
        )
    if payment_method == 'cod':
        _award_loyalty_points(user, total)

    if payment_method == 'gcash':
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
            return redirect(f'/cart-checkout/?error=payment_failed')
    else:
        # COD — clear cart and redirect
        cart_items.delete()
        return redirect('/?order=success')
    
def _award_loyalty_points(user, total_amount):
    """I-award ang loyalty points pagka-confirmed ng order."""
    if not user:
        return
    loyalty, _ = LoyaltyPoint.objects.get_or_create(user=user)
    earned      = loyalty.earn(total_amount)
    return earned
    


def orderSuccess(request):
    # Huwag nang mag-update dito — ang webhook na ang bahala
    # Pero puwede mo pa rin i-show ang success page
    return redirect('/?order=success')


def orderFailed(request):
    order_id = request.GET.get('order_id')
    if order_id:
        order = Order.objects.filter(id=order_id).first()
        if order and order.payment_status == 'unpaid':
            order.payment_status = 'failed'
            order.status         = 'cancelled'
            order.save()
    return redirect('/?order=failed')

