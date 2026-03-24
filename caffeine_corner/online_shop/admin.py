from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
 
from online_shop.models import (
    Category, Product, Variant, Rating,
    Order, CartItem, LoyaltyPoint, OrderItem
)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
 
def _badge(label, bg, fg):
    return format_html(
        '<span style="background:{};color:{};padding:3px 10px;border-radius:5px;'
        'font-size:11px;font-weight:500;white-space:nowrap;">{}</span>',
        bg, fg, label
    )
 
SIZE_ORDER = {"small": 0, "medium": 1, "large": 2}
 
# ─────────────────────────────────────────────────────────────────────────────
# Category
# ─────────────────────────────────────────────────────────────────────────────
 
@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    compressed_fields = True
    list_display      = ["name", "show_active", "sort_order", "product_count"]
    list_filter       = ["is_active"]
    search_fields     = ["name"]
    ordering          = ["sort_order", "name"]
 
    def show_active(self, obj):
        if obj.is_active:
            return _badge("Active", "#eaf5ed", "#2e7d4a")
        return _badge("Inactive", "#fef0ee", "#c04a3a")
    show_active.short_description = _("Status")
 
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = _("Products")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Variant inline
# ─────────────────────────────────────────────────────────────────────────────
 
class VariantInline(TabularInline):
    model  = Variant
    extra  = 0
    fields = ["size", "additional_price", "sku", "barcode"]
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Product
# ─────────────────────────────────────────────────────────────────────────────
 
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_display  = [
        "name", "category", "show_price",
        "show_availability", "show_rating", "is_featured", "is_seasonal",
    ]
    list_filter   = ["category", "is_available", "is_featured", "is_seasonal"]
    search_fields = ["name", "sku", "barcode"]
    ordering      = ["sort_order", "name"]
    inlines       = [VariantInline]
 
    fieldsets = (
        (_("Basic Info"), {
            "fields": ("name", "description", "category", "image"),
            "classes": ("tab",),
        }),
        (_("Pricing"), {
            "fields": ("price", "cost_price", "sku", "barcode"),
            "classes": ("tab",),
        }),
        (_("Visibility"), {
            "fields": ("is_available", "is_featured", "is_seasonal", "sort_order"),
            "classes": ("tab",),
        }),
    )
 
    def show_price(self, obj):
        return format_html(
            '<span style="font-weight:600;">₱{}</span>',
            f"{obj.price:,.2f}"
        )
    show_price.short_description = _("Price")
    show_price.admin_order_field = "price"
 
    def show_availability(self, obj):
        if obj.is_available:
            return _badge("Available", "#eaf5ed", "#2e7d4a")
        return _badge("Unavailable", "#fef0ee", "#c04a3a")
    show_availability.short_description = _("Status")
    show_availability.admin_order_field = "is_available"
 
    def show_rating(self, obj):
        avg = obj.average_rating
        if avg is None:
            return mark_safe('<span style="color:#d3d1c7;">No ratings</span>')
        filled = "★" * round(avg)
        empty  = "☆" * (5 - round(avg))
        return format_html(
            '<span style="color:#c47a2b;font-size:14px;letter-spacing:1px;">{}</span>'
            '<span style="color:#d3d1c7;font-size:14px;letter-spacing:1px;">{}</span>'
            '&nbsp;<span style="font-size:11px;color:#7a6652;">{}</span>',
            filled, empty, avg
        )
    show_rating.short_description = _("Rating")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Variant
# ─────────────────────────────────────────────────────────────────────────────
 
@admin.register(Variant)
class VariantAdmin(ModelAdmin):
    compressed_fields = True
    list_display  = ["product", "show_size", "show_additional_price", "sku"]
    list_filter   = ["size"]
    search_fields = ["product__name", "sku"]
 
    def show_size(self, obj):
        colors = {
            "small":  ("#e6f0fa", "#1a5494"),
            "medium": ("#fff6e0", "#a06010"),
            "large":  ("#eaf5ed", "#2e7d4a"),
        }
        bg, fg = colors.get(obj.size, ("#f1efe8", "#5f5e5a"))
        return _badge(obj.get_size_display(), bg, fg)
    show_size.short_description = _("Size")
    show_size.admin_order_field = "size"
 
    def show_additional_price(self, obj):
        if obj.additional_price == 0:
            return mark_safe('<span style="color:#b4b2a9;">+₱0.00</span>')
        return format_html(
            '<span style="font-weight:500;color:#3d1a00;">+₱{}</span>',
            f"{obj.additional_price:,.2f}"
        )
    show_additional_price.short_description = _("Add. Price")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Rating
# ─────────────────────────────────────────────────────────────────────────────
 
@admin.register(Rating)
class RatingAdmin(ModelAdmin):
    compressed_fields = True
    list_display  = ["product", "user", "show_stars", "review_preview", "created_at"]
    list_filter   = ["rating"]
    search_fields = ["product__name", "user__username"]
    ordering      = ["-created_at"]
    readonly_fields = ["created_at"]
 
    def show_stars(self, obj):
        filled = "★" * obj.rating
        empty  = "☆" * (5 - obj.rating)
        color_map = {5: "#c47a2b", 4: "#c47a2b", 3: "#a06010", 2: "#c04a3a", 1: "#c04a3a"}
        color = color_map.get(obj.rating, "#c47a2b")
        return format_html(
            '<span style="color:{};font-size:16px;letter-spacing:1px;">{}</span>'
            '<span style="color:#d3d1c7;font-size:16px;letter-spacing:1px;">{}</span>',
            color, filled, empty
        )
    show_stars.short_description = _("Rating")
    show_stars.admin_order_field = "rating"
 
    def review_preview(self, obj):
        if not obj.review:
            return mark_safe('<span style="color:#b4b2a9;">—</span>')
        preview = obj.review[:60] + "…" if len(obj.review) > 60 else obj.review
        return format_html('<span style="color:#5f5e5a;">{}</span>', preview)
    review_preview.short_description = _("Review")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Order
# ─────────────────────────────────────────────────────────────────────────────
 
# admin.py

class OrderItemInline(admin.TabularInline):
    model      = OrderItem
    extra      = 0
    readonly_fields = ('product', 'variant', 'quantity', 'price', 'subtotal')

    def subtotal(self, obj):
        return f'₱{obj.subtotal}'
    subtotal.short_description = 'Subtotal'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ('id', 'email', 'status', 'payment_method', 'payment_status', 'item_count', 'total_price', 'created_at')
    list_filter   = ('status', 'payment_method', 'payment_status')
    search_fields = ('email', 'address', 'paymongo_id')
    readonly_fields = ('created_at', 'updated_at', 'total_price', 'item_count')
    inlines       = [OrderItemInline]

    def total_price(self, obj):
        return f'₱{obj.total_price}'
    total_price.short_description = 'Total'

    def item_count(self, obj):
        return obj.item_count
    item_count.short_description = 'Items'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display  = ('order', 'product', 'variant', 'quantity', 'price', 'subtotal')
    list_filter   = ('product__category', 'variant__size')
    search_fields = ('product__name', 'order__email')

    def subtotal(self, obj):
        return f'₱{obj.subtotal}'
    subtotal.short_description = 'Subtotal'
# ─────────────────────────────────────────────────────────────────────────────
# CartItem
# ─────────────────────────────────────────────────────────────────────────────
 
@admin.register(CartItem)
class CartItemAdmin(ModelAdmin):
    compressed_fields = True
    list_display  = ["user", "product", "show_variant", "quantity", "show_subtotal"]
    search_fields = ["user__username", "product__name"]
    list_filter   = ["variant__size"]
 
    def show_variant(self, obj):
        if not obj.variant:
            return mark_safe('<span style="color:#b4b2a9;">—</span>')
        return _badge(obj.variant.get_size_display(), "#f1efe8", "#5f5e5a")
    show_variant.short_description = _("Size")
 
    def show_subtotal(self, obj):
        return format_html(
            '<span style="font-weight:600;">₱{}</span>',
            f"{obj.subtotal:,.2f}"
        )
    show_subtotal.short_description = _("Subtotal")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# LoyaltyPoint
# ─────────────────────────────────────────────────────────────────────────────
 
@admin.register(LoyaltyPoint)
class LoyaltyPointAdmin(ModelAdmin):
    compressed_fields = True
    list_display  = ["user", "show_points", "last_updated"]
    search_fields = ["user__username"]
    ordering      = ["-points"]
    readonly_fields = ["last_updated"]
 
    def show_points(self, obj):
        if obj.points >= 500:
            return _badge(f"{obj.points} pts", "#fff6e0", "#a06010")
        if obj.points >= 100:
            return _badge(f"{obj.points} pts", "#eaf5ed", "#2e7d4a")
        return format_html(
            '<span style="color:#7a6652;font-weight:500;">{} pts</span>',
            obj.points
        )
    show_points.short_description = _("Points")
    show_points.admin_order_field = "points"
