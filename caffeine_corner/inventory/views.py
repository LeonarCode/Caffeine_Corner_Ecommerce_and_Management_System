# inventory/views.py

from django.db.models import Avg, Sum, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from datetime import timedelta

from online_shop.models import Order, OrderItem, Product, Rating, LoyaltyPoint
from inventory.models import Inventory, StockMovement, PurchaseOrder


def dashboard_callback(request, context):

    # ── Online Shop stats ──────────────────────────────────────────────────────

    total_orders = Order.objects.count()

    # Revenue — now from OrderItem since Order no longer has product/quantity
    revenue_qs = OrderItem.objects.filter(
        order__payment_status='paid'
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('price') * F('quantity'),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            )
        )
    )
    total_revenue  = revenue_qs['total'] or 0
    total_products = Product.objects.filter(is_available=True).count()
    avg_raw        = Rating.objects.aggregate(avg=Avg('rating'))['avg']
    avg_rating     = round(avg_raw, 1) if avg_raw else None

    context['stat_cards'] = [
        ('Total Orders',    str(total_orders),                         'receipt_long'),
        ('Revenue',         f'₱{total_revenue:,.0f}',                 'payments'),
        ('Active Products', str(total_products),                       'coffee'),
        ('Avg Rating',      f'{avg_rating} ★' if avg_rating else '—', 'star'),
    ]
    context['total_orders']   = total_orders
    context['total_revenue']  = total_revenue
    context['total_products'] = total_products
    context['avg_rating']     = avg_rating

    # ── Recent orders — no longer has product/variant directly ────────────────
    context['recent_orders'] = (
        Order.objects
        .select_related('user')
        .prefetch_related('items__product', 'items__variant')  # ← use items
        .order_by('-created_at')[:10]
    )

    # ── Low stock items ────────────────────────────────────────────────────────
    context['low_stock_items'] = (
        Inventory.objects
        .select_related('category')
        .filter(quantity_on_hand__lte=F('reorder_points'))
        .order_by('quantity_on_hand')[:5]
    )
    context['low_stock_count'] = (
        Inventory.objects
        .filter(quantity_on_hand__lte=F('reorder_points'))
        .count()
    )

    # ── Inventory monitoring stats ─────────────────────────────────────────────
    stock_value = Inventory.objects.aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity_on_hand') * F('cost_per_unit'),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
    )['total'] or 0
    context['total_stock_value'] = stock_value

    context['out_of_stock_count'] = (
        Inventory.objects.filter(quantity_on_hand=0).count()
    )

    context['pending_po_count'] = (
        PurchaseOrder.objects
        .filter(status__in=['draft', 'sent', 'partial'])
        .count()
    )
    context['pending_purchase_orders'] = (
        PurchaseOrder.objects
        .select_related('supplier')
        .filter(status__in=['draft', 'sent', 'partial'])
        .order_by('-ordered_at')[:5]
    )

    week_ago = timezone.now() - timedelta(days=7)
    context['recent_movements'] = (
        StockMovement.objects
        .select_related('inventory', 'performed_by')
        .filter(created_at__gte=week_ago)
        .order_by('-created_at')[:8]
    )

    # ── Orders per day chart (last 30 days) ───────────────────────────────────
    thirty_days_ago = timezone.now() - timedelta(days=30)

    orders_by_date = (
        Order.objects
        .filter(created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    orders_map = {entry['date']: entry['count'] for entry in orders_by_date}

    chart_labels = []
    chart_data   = []
    for i in range(29, -1, -1):
        day = (timezone.now() - timedelta(days=i)).date()
        chart_labels.append(day.strftime('%b %d'))
        chart_data.append(orders_map.get(day, 0))

    import json
    context['chart_labels'] = json.dumps(chart_labels)
    context['chart_data']   = json.dumps(chart_data)

    context['top_customers'] = (
        LoyaltyPoint.objects
        .select_related('user')
        .order_by('-points')[:5]
    )

    return context
