from django.contrib import admin
from .models import *
import openpyxl
from django.http import HttpResponse
from cart.common.KaveSms import send_sms_normal, send_sms_normal_print
from .services import notify_order_status_change
from django.utils.html import format_html

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

    def save_model(self, request, obj, form, change):
        old_status = None
        if change:
            old_status = Order.objects.get(pk=obj.pk).status

        super().save_model(request, obj, form, change)
        notify_order_status_change(obj, old_status)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity']


class ReturnImageInline(admin.TabularInline):
    model = ReturnImage
    extra = 0
    can_delete = False
    fields = ('preview',)
    readonly_fields = ('preview',)

    @admin.display(description='پیش‌نمایش')
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" style="height:100px"></a>',
                obj.image.url,
            )
        return '-'

    def has_add_permission(self, request, obj=None):
        return False   # ادمین نباید عکس اضافه کند


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_item', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__phone', 'order_item__product__name')
    list_select_related = ('order_item__product', 'user')
    readonly_fields = ('order_item', 'user', 'reason', 'created_at')
    inlines = [ReturnImageInline]
    actions = ['approve_requests', 'reject_requests']

    @admin.action(description='تأیید درخواست‌های انتخاب‌شده')
    def approve_requests(self, request, queryset):
        updated = queryset.filter(status=ReturnRequest.Status.PENDING).update(
            status=ReturnRequest.Status.APPROVED
        )
        self.message_user(request, f'{updated} درخواست تأیید شد.', messages.SUCCESS)

    @admin.action(description='رد درخواست‌های انتخاب‌شده')
    def reject_requests(self, request, queryset):
        updated = queryset.filter(status=ReturnRequest.Status.PENDING).update(
            status=ReturnRequest.Status.REJECTED
        )
        self.message_user(request, f'{updated} درخواست رد شد.', messages.SUCCESS)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'valid_from', 'valid_to', 'is_active']
    list_filter = ['discount_percent', 'valid_from', 'valid_to', 'is_active']
