from django.contrib import admin
from .models import *


class ImageInline(admin.StackedInline):
    model = Image
    extra = 0

class FeatureInline(admin.StackedInline):
    model = ProductFeature
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'inventory', 'created', 'updated']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['category', 'created', 'updated']
    search_fields = ['name', 'description']
    inlines = [ImageInline, FeatureInline]
