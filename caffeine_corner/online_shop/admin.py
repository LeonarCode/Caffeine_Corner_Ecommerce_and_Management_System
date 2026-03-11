from django.contrib import admin
from .models import Product, Category, Order, Variant, Rating
from unfold.admin import ModelAdmin


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'sort_order')
    search_fields = ('name', 'description')
    list_filter = ('is_active', 'sort_order')
    list_editable = ('is_active', 'sort_order')
    list_per_page = 10
    list_max_show_all = 100
    list_max_show_all = 100
    list_per_page = 10

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_available', 'is_featured', 'is_seasonal')
    search_fields = ('name', 'category__name')
    list_filter = ('category', 'is_available', 'is_featured', 'is_seasonal')
    list_editable = ('is_available', 'is_featured', 'is_seasonal')
    list_per_page = 10
    list_max_show_all = 100
    list_max_show_all = 100
    list_per_page = 10

@admin.register(Variant)
class VariantAdmin(ModelAdmin):
    list_display = ('product', 'size', 'additional_price')
    search_fields = ('product__name', 'size')
    list_filter = ('product', 'size')
    list_editable = ('additional_price',)
    list_per_page = 10
    list_max_show_all = 100
    list_max_show_all = 100
    list_per_page = 10

@admin.register(Rating)
class RatingAdmin(ModelAdmin):
    list_display = ('product', 'user', 'rating', 'review', 'created_at')
    list_filter = ('product', 'rating')


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('user', 'product', 'variant', 'quantity', 'created_at', 'updated_at')
    search_fields = ('user__username', 'product__name', 'variant__size')
    list_filter = ('user', 'product', 'variant')
    list_editable = ('quantity',)
    list_per_page = 10
    list_max_show_all = 100
    list_max_show_all = 100
    list_per_page = 10
    list_display = ('user', 'product', 'variant', 'quantity', 'created_at', 'updated_at')
    search_fields = ('user__username', 'product__name', 'variant__size')
    list_filter = ('user', 'product', 'variant')
    list_editable = ('quantity',)
    list_per_page = 10
    list_max_show_all = 100
    list_max_show_all = 100
    list_per_page = 10
