import datetime
from django.db import models
from django.db.models.fields import PositiveIntegerField
from django.utils import timezone
from account.models import ShopUser
from shop.models import Product

# Create your models here.
RETURN_DAYS = 3
class Order(models.Model):
    buyer = models.ForeignKey(ShopUser, related_name='Orders', on_delete=models.SET_NULL, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=11)
    address = models.CharField(max_length=250)
    postcode = models.CharField(max_length=10)
    province = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    authority = models.CharField(max_length=255, null=True, blank=True, unique=True)

    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار پرداخت'
        CONFIRMED = 'confirmed', 'تأیید شده'
        PROCESSING = 'processing', 'در حال آماده‌سازی'
        CANCELLED = 'cancelled', 'لغو شده'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"order {self.id}"

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_post_cost(self):
        weight = sum(item.get_weight() for item in self.items.all())
        if weight < 1000:
            return 20000
        elif 1000 <= weight < 2000:
            return 30000
        else:
            return 50000

    def get_final_cost(self):
        price = self.get_post_cost() + self.get_total_cost()
        return price

    @property
    def can_return(self):
        age = timezone.now() - self.created_at
        if self.paid and age <= datetime.timedelta(days=RETURN_DAYS):
            return True
        return False


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=1)
    weight = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.quantity * self.price

    def get_weight(self):
        return self.weight * self.quantity

    @property
    def can_request_return(self):
        has_active = self.return_requests.filter(
            status__in=[ReturnRequest.Status.PENDING, ReturnRequest.Status.APPROVED]
        ).exists()
        return self.order.can_return and not has_active


class Transaction(models.Model):
    gateway_transaction_id = models.CharField(max_length=100, unique=True, verbose_name='شناسه تراکنش درگاه')
    order = models.ForeignKey(Order, related_name='transactions', on_delete=models.CASCADE)
    price = models.PositiveIntegerField(default=0, verbose_name='مبلغ تراکنش')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ تراکنش')


class ReturnRequest(models.Model):
    order_item = models.ForeignKey(OrderItem, related_name='return_requests', on_delete=models.PROTECT)
    user = models.ForeignKey(ShopUser, related_name='return_requests', on_delete=models.CASCADE)
    reason = models.TextField()
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار بررسی'
        APPROVED = 'approved', 'تأیید شده'
        REJECTED = 'rejected', 'رد شده'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Return #{self.id} - {self.order_item.product.name}'


class ReturnImage(models.Model):
    return_request = models.ForeignKey(ReturnRequest, related_name='return_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='return_images/%Y/%m/', blank=True)

    def __str__(self):
        return f'Image for return #{self.return_request_id}'