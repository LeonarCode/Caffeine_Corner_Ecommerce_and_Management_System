from django.db.models import Avg, Sum, Count, F, ExpressionWrapper, DecimalField
 
from online_shop.models import Order, Product, Rating, LoyaltyPoint
from inventory.models import Inventory
 
 
def dashboard_callback(request, context):
    """
    Populates context for templates/unfold/welcome.html.
    Called automatically by Unfold via UNFOLD["DASHBOARD_CALLBACK"].
    """
 
    # ── Raw aggregates ─────────────────────────────────────────────────────────
 
    total_orders = Order.objects.count()
 
    # Revenue: (product.price + variant.additional_price) * quantity
    # variant.additional_price may be NULL for orders without a variant,
    # so we use Coalesce to fall back to 0
    from django.db.models.functions import Coalesce
    revenue_qs = Order.objects.annotate(
        unit_price=ExpressionWrapper(
            F("product__price") + Coalesce(
                F("variant__additional_price"),
                0,
                output_field=DecimalField()
            ),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F("unit_price") * F("quantity"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            )
        )
    )
    total_revenue = revenue_qs["total"] or 0
 
    total_products = Product.objects.filter(is_available=True).count()
 
    avg_raw = Rating.objects.aggregate(avg=Avg("rating"))["avg"]
    avg_rating = round(avg_raw, 1) if avg_raw else None
 
    # ── Stat cards (label, display value, material icon name) ──────────────────
    context["stat_cards"] = [
        ("Total Orders",    str(total_orders),                          "receipt_long"),
        ("Revenue",         f"₱{total_revenue:,.0f}",                  "payments"),
        ("Active Products", str(total_products),                        "coffee"),
        ("Avg Rating",      f"{avg_rating} ★" if avg_rating else "—",  "star"),
    ]
 
    # Also expose raw values for any custom template logic
    context["total_orders"]   = total_orders
    context["total_revenue"]  = total_revenue
    context["total_products"] = total_products
    context["avg_rating"]     = avg_rating
 
    # ── Recent orders (last 10) ────────────────────────────────────────────────
    context["recent_orders"] = (
        Order.objects
        .select_related("user", "product", "variant")
        .order_by("-created_at")[:10]
    )
 
    # ── Low stock ──────────────────────────────────────────────────────────────
    context["low_stock_items"] = (
        Inventory.objects
        .select_related("category")
        .filter(quantity_on_hand__lte=F("reorder_points"))
        .order_by("quantity_on_hand")[:5]
    )
    context["low_stock_count"] = (
        Inventory.objects
        .filter(quantity_on_hand__lte=F("reorder_points"))
        .count()
    )
 
    # ── Top customers by loyalty points ───────────────────────────────────────
    context["top_customers"] = (
        LoyaltyPoint.objects
        .select_related("user")
        .order_by("-points")[:5]
    )
 
    return context
