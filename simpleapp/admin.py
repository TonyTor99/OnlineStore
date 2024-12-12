from django.contrib import admin
from .models import Product, Category


class ProductAdmin(admin.ModelAdmin):

    def nullfy_quantity(modeladmin, request, queryset):  # все аргументы уже должны быть вам знакомы, самые нужные из
        # них это request —
        # объект хранящий информацию о запросе и queryset — грубо говоря набор объектов, которых мы выделили галочками.
        queryset.update(quantity=0)
    nullfy_quantity.short_description = 'Обнулить товары'  # описание для более понятного представления в админ
    # панеле задаётся, как будто это объект

    # list_display = [field.name for field in Product._meta.get_fields()]
    list_display = ('name', 'price', 'quantity', 'on_stock')
    list_filter = ('price', 'quantity', 'name')
    search_fields = ('name', 'category__name')
    actions = [nullfy_quantity]


admin.site.register(Product, ProductAdmin)
admin.site.register(Category)
