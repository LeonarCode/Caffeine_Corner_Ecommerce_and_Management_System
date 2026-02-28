from django.contrib import admin
from django.contrib.auth.models import User
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm, SelectableFieldsExportForm
from .models import InventoryCategory, Inventory, Ingredient
from online_shop.models import Product, Variant, Category
# Register your models here.

admin.site.unregister(User)

@admin.register(User)
class UserAdmin(ModelAdmin, BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

@admin.register(Inventory)
class InventoryAdmin(ImportExportModelAdmin):
    list_display = ('name', 'sku', 'quantity_on_hand', 'quantity_reserved', 'reorder_points', 'reorder_quantity', 'last_updated')
    search_fields = ('name', 'sku')
    list_filter = ('category',)
    import_form_class = ImportForm
    export_form_class = ExportForm