# inventory/admin.py

from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.urls import reverse
from django.utils import timezone
from unfold.admin import ModelAdmin, TabularInline, StackedInline

from inventory.models import (
    InventoryCategory,
    Inventory,
    Supplier,
    StockMovement,
    PurchaseOrder,
    PurchaseOrderItem,
    Ingredient,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _badge(label, bg, fg):
    return format_html(
        '<span style="background:{};color:{};padding:3px 10px;border-radius:5px;'
        'font-size:11px;font-weight:500;white-space:nowrap;">{}</span>',
        bg, fg, label,
    )


def _stock_bar(qty_on_hand, reorder_points):
    """Renders a mini progress bar showing stock vs reorder point."""
    if reorder_points == 0:
        pct = 100
    else:
        pct = min(int((qty_on_hand / reorder_points) * 50), 100)

    if qty_on_hand <= reorder_points:
        color = "#c04a3a"
    elif qty_on_hand <= reorder_points * 2:
        color = "#a06010"
    else:
        color = "#2e7d4a"

    return format_html(
        '<div style="display:flex;align-items:center;gap:8px;min-width:120px;">'
        '  <div style="flex:1;height:6px;background:#e8ddd0;border-radius:3px;overflow:hidden;">'
        '    <div style="width:{}%;height:100%;background:{};border-radius:3px;'
        '         transition:width .3s;"></div>'
        '  </div>'
        '  <span style="font-size:12px;font-weight:500;color:{};">{}</span>'
        '</div>',
        pct, color, color, qty_on_hand,
    )


# ─────────────────────────────────────────────────────────────────────────────
# InventoryCategory
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(InventoryCategory)
class InventoryCategoryAdmin(ModelAdmin):
    compressed_fields = True
    list_display  = ["name", "description", "item_count"]
    search_fields = ["name"]

    def item_count(self, obj):
        count = obj.items.count()
        return format_html('<span style="font-weight:500;">{}</span>', count)
    item_count.short_description = _("Items")


# ─────────────────────────────────────────────────────────────────────────────
# Supplier
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Supplier)
class SupplierAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_display  = [
        "name", "contact_name", "email", "phone",
        "show_status", "item_count", "po_count",
    ]
    list_filter   = ["is_active"]
    search_fields = ["name", "contact_name", "email"]
    ordering      = ["name"]

    fieldsets = (
        (_("Supplier Info"), {
            "fields": ("name", "contact_name", "is_active"),
            "classes": ("tab",),
        }),
        (_("Contact"), {
            "fields": ("email", "phone", "address"),
            "classes": ("tab",),
        }),
        (_("Notes"), {
            "fields": ("notes",),
            "classes": ("tab",),
        }),
    )

    def show_status(self, obj):
        if obj.is_active:
            return _badge("Active", "#eaf5ed", "#2e7d4a")
        return _badge("Inactive", "#fef0ee", "#c04a3a")
    show_status.short_description = _("Status")
    show_status.admin_order_field = "is_active"

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = _("Items")

    def po_count(self, obj):
        count = obj.purchase_orders.count()
        if count == 0:
            return mark_safe('<span style="color:#b4b2a9;">—</span>')
        url = reverse("admin:inventory_purchaseorder_changelist") + f"?supplier__id={obj.pk}"
        return format_html('<a href="{}" style="color:rgb(160 105 55);font-weight:500;">{} POs</a>', url, count)
    po_count.short_description = _("Purchase Orders")


# ─────────────────────────────────────────────────────────────────────────────
# Stock Movement inline
# ─────────────────────────────────────────────────────────────────────────────

class StockMovementInline(TabularInline):
    model   = StockMovement
    extra   = 0
    fields  = ["movement_type", "quantity", "unit_cost", "reference", "notes", "performed_by", "created_at"]
    readonly_fields = ["created_at", "quantity_change"]
    ordering = ["-created_at"]
    max_num = 10

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("performed_by")


# ─────────────────────────────────────────────────────────────────────────────
# Ingredient inline
# ─────────────────────────────────────────────────────────────────────────────

class IngredientInline(TabularInline):
    model  = Ingredient
    extra  = 0
    fields = ["product", "quantity", "unit", "notes"]


# ─────────────────────────────────────────────────────────────────────────────
# Inventory
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Inventory)
class InventoryAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth    = True

    list_display = [
        "name", "category", "supplier",
        "show_stock_bar", "show_reserved",
        "show_stock_status", "show_stock_value",
        "last_updated",
    ]
    list_filter   = ["category", "supplier"]
    search_fields = ["name", "sku"]
    ordering      = ["category__name", "name"]
    readonly_fields = ["last_updated", "show_stock_summary"]

    fieldsets = (
        (_("Item Info"), {
            "fields": ("name", "sku", "unit", "category", "supplier"),
            "classes": ("tab",),
        }),
        (_("Stock Levels"), {
            "fields": (
                "show_stock_summary",
                "quantity_on_hand", "quantity_reserved",
                "reorder_points", "reorder_quantity",
            ),
            "classes": ("tab",),
        }),
        (_("Costing"), {
            "fields": ("cost_per_unit",),
            "classes": ("tab",),
        }),
    )

    inlines = [StockMovementInline, IngredientInline]

    def show_stock_bar(self, obj):
        return _stock_bar(obj.quantity_on_hand, obj.reorder_points)
    show_stock_bar.short_description = _("Stock Level")

    def show_reserved(self, obj):
        if obj.quantity_reserved == 0:
            return mark_safe('<span style="color:#b4b2a9;">—</span>')
        return format_html(
            '<span style="color:#a06010;font-weight:500;">{} {}</span>',
            obj.quantity_reserved, obj.unit,
        )
    show_reserved.short_description = _("Reserved")

    def show_stock_status(self, obj):
        if obj.quantity_on_hand == 0:
            return _badge("Out of Stock", "#fef0ee", "#c04a3a")
        if obj.is_low_stock:
            return _badge("Low Stock", "#fff6e0", "#a06010")
        return _badge("OK", "#eaf5ed", "#2e7d4a")
    show_stock_status.short_description = _("Status")

    def show_stock_value(self, obj):
        value = obj.stock_value
        if value == 0:
            return mark_safe('<span style="color:#b4b2a9;">₱0.00</span>')
        return format_html(
            '<span style="font-weight:600;">₱{}</span>',
            f"{value:,.2f}",
        )
    show_stock_value.short_description = _("Stock Value")

    def show_stock_summary(self, obj):
        """Rich summary card shown at top of the stock levels tab."""
        avail = obj.quantity_available
        if obj.reorder_points > 0:
            pct = min(int((obj.quantity_on_hand / obj.reorder_points) * 100), 200)
        else:
            pct = 100
        bar_color = "#c04a3a" if obj.is_low_stock else "#2e7d4a"
        bar_pct   = min(pct, 100)

        return format_html(
            '<div style="display:grid;grid-template-columns:repeat(3,1fr);'
            'gap:12px;margin-bottom:16px;">'

            '<div style="background:#faf7f2;border:1px solid #e8ddd0;'
            'border-radius:8px;padding:12px 16px;">'
            '<p style="font-size:10px;text-transform:uppercase;letter-spacing:1px;'
            'color:#7a6652;margin:0 0 4px;">On Hand</p>'
            '<p style="font-size:22px;font-weight:700;color:#1a0a00;margin:0;">'
            '{} <span style="font-size:12px;color:#7a6652;">{}</span></p>'
            '</div>'

            '<div style="background:#faf7f2;border:1px solid #e8ddd0;'
            'border-radius:8px;padding:12px 16px;">'
            '<p style="font-size:10px;text-transform:uppercase;letter-spacing:1px;'
            'color:#7a6652;margin:0 0 4px;">Available</p>'
            '<p style="font-size:22px;font-weight:700;color:#1a0a00;margin:0;">'
            '{} <span style="font-size:12px;color:#7a6652;">{}</span></p>'
            '</div>'

            '<div style="background:#faf7f2;border:1px solid #e8ddd0;'
            'border-radius:8px;padding:12px 16px;">'
            '<p style="font-size:10px;text-transform:uppercase;letter-spacing:1px;'
            'color:#7a6652;margin:0 0 4px;">Reorder Point</p>'
            '<p style="font-size:22px;font-weight:700;color:#1a0a00;margin:0;">'
            '{} <span style="font-size:12px;color:#7a6652;">{}</span></p>'
            '</div>'

            '</div>'
            '<div style="margin-bottom:8px;">'
            '<div style="height:8px;background:#e8ddd0;border-radius:4px;overflow:hidden;">'
            '<div style="width:{}%;height:100%;background:{};border-radius:4px;"></div>'
            '</div>'
            '<p style="font-size:11px;color:#7a6652;margin:4px 0 0;">{}% of reorder point</p>'
            '</div>',
            obj.quantity_on_hand, obj.unit,
            avail, obj.unit,
            obj.reorder_points, obj.unit,
            bar_pct, bar_color,
            pct,
        )
    show_stock_summary.short_description = _("Stock Summary")


# ─────────────────────────────────────────────────────────────────────────────
# Stock Movement
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(StockMovement)
class StockMovementAdmin(ModelAdmin):
    compressed_fields = True
    list_fullwidth    = True
    list_display  = [
        "created_at", "inventory", "show_type",
        "show_quantity_change", "unit_cost",
        "reference", "performed_by",
    ]
    list_filter   = ["movement_type", "created_at", "inventory__category"]
    search_fields = ["inventory__name", "reference", "notes"]
    ordering      = ["-created_at"]
    date_hierarchy = "created_at"
    readonly_fields = ["quantity_change", "created_at"]

    fieldsets = (
        (_("Movement"), {
            "fields": (
                "inventory", "movement_type",
                "quantity", "quantity_change", "unit_cost",
            ),
            "classes": ("tab",),
        }),
        (_("Details"), {
            "fields": ("reference", "notes", "performed_by", "created_at"),
            "classes": ("tab",),
        }),
    )

    TYPE_COLORS = {
        "purchase":   ("#eaf5ed", "#2e7d4a"),
        "return":     ("#eaf5ed", "#2e7d4a"),
        "transfer":   ("#e6f0fa", "#1a5494"),
        "usage":      ("#fff6e0", "#a06010"),
        "adjustment": ("#f1efe8", "#5f5e5a"),
        "spoilage":   ("#fef0ee", "#c04a3a"),
    }

    def show_type(self, obj):
        bg, fg = self.TYPE_COLORS.get(obj.movement_type, ("#f1efe8", "#5f5e5a"))
        return _badge(obj.get_movement_type_display(), bg, fg)
    show_type.short_description = _("Type")
    show_type.admin_order_field = "movement_type"

    def show_quantity_change(self, obj):
        val = obj.quantity_change
        unit = obj.inventory.unit
        if val > 0:
            return format_html(
                '<span style="color:#2e7d4a;font-weight:600;">+{} {}</span>',
                val, unit,
            )
        return format_html(
            '<span style="color:#c04a3a;font-weight:600;">{} {}</span>',
            val, unit,
        )
    show_quantity_change.short_description = _("Change")
    show_quantity_change.admin_order_field = "quantity_change"

    def save_model(self, request, obj, form, change):
        if not obj.performed_by_id:
            obj.performed_by = request.user
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────────────────────────────────────────
# Purchase Order Items inline
# ─────────────────────────────────────────────────────────────────────────────

class PurchaseOrderItemInline(TabularInline):
    model   = PurchaseOrderItem
    extra   = 1
    fields  = [
        "inventory", "quantity_ordered", "quantity_received",
        "unit_cost", "show_total", "show_received_status",
    ]
    readonly_fields = ["show_total", "show_received_status"]

    def show_total(self, obj):
        if not obj.pk:
            return mark_safe('<span style="color:#b4b2a9;">—</span>')
        return format_html(
            '<span style="font-weight:600;">₱{}</span>',
            f"{obj.total_cost:,.2f}",
        )
    show_total.short_description = _("Total")

    def show_received_status(self, obj):
        if not obj.pk:
            return mark_safe('<span style="color:#b4b2a9;">—</span>')
        if obj.is_fully_received:
            return _badge("Received", "#eaf5ed", "#2e7d4a")
        if obj.quantity_received > 0:
            return _badge("Partial", "#fff6e0", "#a06010")
        return _badge("Pending", "#f1efe8", "#5f5e5a")
    show_received_status.short_description = _("Receipt")


# ─────────────────────────────────────────────────────────────────────────────
# Purchase Order
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_fullwidth    = True

    list_display  = [
        "reference", "supplier", "show_status",
        "ordered_at", "expected_at", "received_at",
        "show_total_cost", "show_item_count",
    ]
    list_filter   = ["status", "supplier", "ordered_at"]
    search_fields = ["reference", "supplier__name", "notes"]
    ordering      = ["-ordered_at"]
    date_hierarchy = "ordered_at"
    readonly_fields = ["ordered_at", "show_po_summary"]

    fieldsets = (
        (_("Purchase Order"), {
            "fields": ("reference", "supplier", "status", "show_po_summary"),
            "classes": ("tab",),
        }),
        (_("Dates"), {
            "fields": ("ordered_at", "expected_at", "received_at"),
            "classes": ("tab",),
        }),
        (_("Notes"), {
            "fields": ("notes", "created_by"),
            "classes": ("tab",),
        }),
    )

    inlines = [PurchaseOrderItemInline]

    STATUS_COLORS = {
        "draft":     ("#f1efe8", "#5f5e5a"),
        "sent":      ("#e6f0fa", "#1a5494"),
        "partial":   ("#fff6e0", "#a06010"),
        "received":  ("#eaf5ed", "#2e7d4a"),
        "cancelled": ("#fef0ee", "#c04a3a"),
    }

    def show_status(self, obj):
        bg, fg = self.STATUS_COLORS.get(obj.status, ("#f1efe8", "#5f5e5a"))
        return _badge(obj.get_status_display(), bg, fg)
    show_status.short_description = _("Status")
    show_status.admin_order_field = "status"

    def show_total_cost(self, obj):
        total = obj.total_cost
        if total == 0:
            return mark_safe('<span style="color:#b4b2a9;">₱0.00</span>')
        return format_html(
            '<span style="font-weight:600;">₱{}</span>',
            f"{total:,.2f}",
        )
    show_total_cost.short_description = _("Total Cost")

    def show_item_count(self, obj):
        count = obj.items.count()
        return format_html(
            '<span style="font-weight:500;">{} item{}</span>',
            count, "s" if count != 1 else "",
        )
    show_item_count.short_description = _("Items")

    def show_po_summary(self, obj):
        if not obj.pk:
            return mark_safe('<span style="color:#b4b2a9;">Save first to see summary.</span>')

        total = obj.total_cost
        item_count = obj.items.count()
        received = obj.items.filter(
            quantity_received__gte=F("quantity_ordered")
        ).count()

        bg, fg = self.STATUS_COLORS.get(obj.status, ("#f1efe8", "#5f5e5a"))

        return format_html(
            '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:8px;">'

            '<div style="background:#faf7f2;border:1px solid #e8ddd0;'
            'border-radius:8px;padding:12px 16px;min-width:120px;">'
            '<p style="font-size:10px;text-transform:uppercase;letter-spacing:1px;'
            'color:#7a6652;margin:0 0 4px;">Total Cost</p>'
            '<p style="font-size:20px;font-weight:700;color:#1a0a00;margin:0;">₱{}</p>'
            '</div>'

            '<div style="background:#faf7f2;border:1px solid #e8ddd0;'
            'border-radius:8px;padding:12px 16px;min-width:120px;">'
            '<p style="font-size:10px;text-transform:uppercase;letter-spacing:1px;'
            'color:#7a6652;margin:0 0 4px;">Items</p>'
            '<p style="font-size:20px;font-weight:700;color:#1a0a00;margin:0;">{}</p>'
            '</div>'

            '<div style="background:#faf7f2;border:1px solid #e8ddd0;'
            'border-radius:8px;padding:12px 16px;min-width:120px;">'
            '<p style="font-size:10px;text-transform:uppercase;letter-spacing:1px;'
            'color:#7a6652;margin:0 0 4px;">Received</p>'
            '<p style="font-size:20px;font-weight:700;color:#1a0a00;margin:0;">{}/{}</p>'
            '</div>'

            '<div style="background:{};border-radius:8px;padding:12px 16px;">'
            '<p style="font-size:10px;text-transform:uppercase;letter-spacing:1px;'
            'color:{};margin:0 0 4px;">Status</p>'
            '<p style="font-size:14px;font-weight:600;color:{};margin:0;">{}</p>'
            '</div>'

            '</div>',
            f"{total:,.2f}",
            item_count,
            received, item_count,
            bg, fg, fg, obj.get_status_display(),
        )
    show_po_summary.short_description = _("Summary")

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────────────────────────────────────────
# Ingredient
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Ingredient)
class IngredientAdmin(ModelAdmin):
    compressed_fields = True
    list_display  = ["product", "inventory", "quantity", "unit", "notes"]
    search_fields = ["product__name", "inventory__name"]
    list_filter   = ["inventory__category"]
    ordering      = ["product__name"]

