from django.contrib import admin
from .models import Order, OrderItem
import openpyxl
from django.http import HttpResponse

# Register your models here.

@admin.action(description='export to excel')
def export_to_excel(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="orders.xlsx"'
    # ------------------------
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Orders'
    # ------------------------
    columns = ['id', 'buyer', 'first_name', 'last_name', 'phone', 'address', 'postcode',
               'province', 'city', 'paid', 'created_at']
    ws.append(columns)
    # ------------------------
    for order in queryset:
        created = order.created_at.replace(tzinfo=None) if order.created_at else ''
        ws.append([order.id, order.buyer.phone if order.buyer else '', order.first_name, order.last_name, order.phone, order.address,
                   order.postcode, order.province, order.city, order.paid, created])
    wb.save(response)
    return response


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ('product', )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'buyer', 'first_name', 'last_name', 'phone', 'address', 'postcode', 'province', 'city',
                    'paid', 'status', 'created_at', 'updated_at']
    list_filter = ['paid', 'status', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    actions = [export_to_excel]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity']
