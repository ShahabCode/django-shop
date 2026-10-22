from django.utils import timezone
import datetime
from pydoc import describe
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import PhoneVerificationForm, OrderCreateForm, OrderStatusForm
from account.models import ShopUser
from .models import OrderItem, Order
from cart.cart import Cart
import random
from django.contrib.auth import authenticate, login, logout
from cart.common.KaveSms import send_sms_with_template
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse
import requests
import json
from .services import notify_order_status_change


# Create your views here.
def verify_phone(request):
    if request.user.is_authenticated:
        return redirect('orders:order_create')
    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            if ShopUser.objects.filter(phone=phone).exists():
                messages.error(request, 'this phone already registered')
                return redirect('orders:verify_phone')
            else:
                tokens = {'token': ''.join(random.choices('0123456789', k=6))}
                token_expiry = timezone.now() + datetime.timedelta(minutes=1)
                request.session['verification_expiry'] = token_expiry.isoformat()
                request.session['verification_code'] = tokens['token']
                request.session['verification_attempts'] = 0
                request.session['phone'] = phone
                print(tokens)
                # send_sms_with_template(phone, tokens, 'verify')
                messages.error(request, 'verification code sent successfully')
                return redirect('orders:verify_code')
    else:
        form = PhoneVerificationForm()

    return render(request, 'verify_phone.html', {'form': form})


def verify_code(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        if code:
            verification_code = request.session.get('verification_code')
            phone = request.session.get('phone')
            expiry = request.session.get('verification_expiry')
            attempts = request.session.get('verification_attempts', 0)

            if not expiry or timezone.now() >= datetime.datetime.fromisoformat(expiry):
                request.session.pop('verification_code', None)
                request.session.pop('phone', None)
                request.session.pop('verification_expiry', None)
                request.session.pop('verification_attempts', None)

                messages.error(request, 'verification code expired')
                return redirect('orders:verify_phone')

            if attempts >= 5:
                request.session.pop('verification_attempts', None)
                request.session.pop('phone', None)
                request.session.pop('verification_expiry', None)
                request.session.pop('verification_code', None)

                messages.error(request, 'Too many attempts. Please request a new code.')
                return redirect('orders:verify_phone')

            if code == verification_code:
                user = ShopUser.objects.create_user(phone=phone)
                user.set_password(phone)
                user.save()
                # sms
                print(user)
                login(request, user)
                del request.session['verification_code']
                del request.session['phone']
                del request.session['verification_expiry']
                del request.session['verification_attempts']
                return redirect('orders:order_create')
            else:
                attempts += 1
                request.session['verification_attempts'] = attempts
                remaining = 5 - attempts
                messages.error(request, f'invalid verification code. remaining: {remaining}')

    expiry = request.session.get('verification_expiry')
    remaining_seconds = 0

    if expiry:
        expiry_time = datetime.datetime.fromisoformat(expiry)
        remaining_seconds = max(
            0,
            int((expiry_time - timezone.now()).total_seconds())
        )

    return render(request, 'verify_code.html', {
        'remaining_seconds': remaining_seconds,
    })


@login_required
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            order.buyer = request.user
            order.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item["product"], quantity=item["quantity"],
                                         price=item["price"], weight=item["weight"])
            cart.clear()
            request.session['order_id'] = order.id
            return redirect('orders:request')
    else:
        form = OrderCreateForm()
    return render(request, 'order_create.html', {'form': form, 'cart': cart})



# ? sandbox merchant
if settings.SANDBOX:
    ZP_API_REQUEST = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
    ZP_API_VERIFY = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
    ZP_API_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay/"
else:
    ZP_API_REQUEST = "https://payment.zarinpal.com/pg/v4/payment/request.json"
    ZP_API_VERIFY = "https://payment.zarinpal.com/pg/v4/payment/verify.json"
    ZP_API_STARTPAY = "https://www.zarinpal.com/pg/StartPay/"

CallbackURL = 'http://127.0.0.1:8000/order/verify/'


def send_request(request):
    order = Order.objects.get(id=request.session['order_id'])

    description = ", ".join(
        item.product.name for item in order.items.all()
    )

    if not description:
        description = f"پرداخت سفارش شماره {order.id}"

    data = {
        "merchant_id": settings.MERCHANT,
        "amount": int(order.get_final_cost()),
        "description": description[:500],
        "callback_url": CallbackURL,
        "metadata": {
            "mobile": request.user.phone,
        },
    }

    try:
        response = requests.post(
            ZP_API_REQUEST,
            json=data,
            timeout=10,
        )

        response_json = response.json()
        print(response.status_code, response_json)

        if response.status_code == 200:
            if response_json.get("data", {}).get("code") == 100:
                authority = response_json["data"]["authority"]
                return redirect(ZP_API_STARTPAY + authority)

        return HttpResponse(
            f"Payment error: {response_json}"
        )

    except requests.exceptions.Timeout:
        return HttpResponse("Timeout Error")

    except requests.exceptions.ConnectionError:
        return HttpResponse("Connection Error")

    except ValueError:
        return HttpResponse("Invalid JSON response from Zarinpal")


def verify(request):
    order = Order.objects.get(id=request.session['order_id'])

    authority = request.GET.get("Authority")
    status = request.GET.get("Status")

    if status != "OK" or not authority:
        return render(
            request,
            "payment-tracking.html",
            {"success": False},
        )

    data = {
        "merchant_id": settings.MERCHANT,
        "amount": int(order.get_final_cost()),
        "authority": authority,
    }

    try:
        response = requests.post(
            ZP_API_VERIFY,
            json=data,
            timeout=10,
        )

        response_json = response.json()
        print(response.status_code, response_json)

        code = response_json.get("data", {}).get("code")

        if response.status_code == 200 and code in (100, 101):
            # جلوگیری از کم شدن دوباره موجودی
            if not order.paid:
                for item in order.items.all():
                    item.product.inventory -= item.quantity
                    item.product.save()

                order.paid = True
                order.save()

            reference_id = response_json["data"].get("ref_id")

            request.session.pop("order_id", None)

            return render(
                request,
                "payment-tracking.html",
                {
                    "success": True,
                    "RefID": reference_id,
                    "order_id": order.id,
                },
            )

        return render(
            request,
            "payment-tracking.html",
            {"success": False},
        )

    except requests.exceptions.Timeout:
        return HttpResponse("Timeout Error")

    except requests.exceptions.ConnectionError:
        return HttpResponse("Connection Error")

    except ValueError:
        return HttpResponse("Invalid JSON response from Zarinpal")

@login_required
def orders_list(request):
    user = request.user
    orders = Order.objects.filter(buyer=user)
    return render(request, 'orders_list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    user = request.user
    order = get_object_or_404(Order, id=order_id, buyer=user)
    return render(request, 'order_detail.html', {'order': order})



@staff_member_required
def change_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)

        if form.is_valid():
            old_status = Order.objects.get(pk=order.pk).status
            updated_order = form.save()

            notify_order_status_change(updated_order, old_status)

            return redirect('orders:order_detail', order_id=order.id)
    else:
        form = OrderStatusForm(instance=order)

    return render(request,'change_order_status.html',{'form': form, 'order': order})
