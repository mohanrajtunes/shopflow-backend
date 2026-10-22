from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, Product, CartItem, Order, OrderItem


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Shop info", {"fields": ("role", "phone_number")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Shop info", {"fields": ("role", "phone_number")}),
    )
    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role", "is_staff")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "vendor", "category", "price", "stock")
    list_filter = ("category", "vendor")
    search_fields = ("title",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "total_price", "created_at")
    list_filter = ("status",)
    inlines = [OrderItemInline]


admin.site.register(CartItem)