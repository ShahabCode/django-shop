import datetime
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.utils.text import phone2numeric
from django.views.decorators.http import require_POST
from django.contrib import messages
from .otp import *
from orders.forms import PhoneVerificationForm
from .forms import ShopUserCreationForm, AddressForm
from .models import Address, ShopUser


# Create your views here.
def register(request):
    if request.method == 'POST':
        form = ShopUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('shop:products')
    else:
        form = ShopUserCreationForm()

    return render(request, 'account/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        user = authenticate(request, username=phone, password=password)

        if user is not None:
            login(request, user)
            return redirect('shop:products')

        return render(request, 'account/login.html', {'error': 'شماره موبایل یا رمز عبور اشتباه است'})

    return render(request, 'account/login.html')


def user_logout(request):
    logout(request)
    return redirect('shop:products')


@login_required
def address_list(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect('account:address_list')
    else:
        form = AddressForm()

    addresses = request.user.addresses.all()
    context = {'form': form, 'addresses': addresses}

    return render(request, 'account/address_list.html', context)


@login_required
@require_POST
def set_default_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, 'آدرس پیش فرض تغییر کرد')
    return redirect('account:address_list')


def otp_request(request):
    if request.user.is_authenticated:
        return redirect('shop:products')

    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)

        if form.is_valid():
            otp_code = generate_code()
            print(otp_code)
            phone = form.cleaned_data['phone']
            request.session['phone'] = phone
            request.session['verification_code'] = otp_code
            request.session['verification_attempts'] = 0
            expiry = timezone.now() + datetime.timedelta(minutes=2)
            request.session['verification_expiry'] = expiry.isoformat()
            return redirect('account:otp_verify')

    else:
        form = PhoneVerificationForm()
    return render(request, 'account/otp_request.html', {'form': form})


def otp_verify(request):
    if request.user.is_authenticated:
        return redirect('shop:products')

    if not request.session.get('phone'):
        return redirect('account:otp_request')

    if request.method == 'POST':
        code = request.POST.get('code')

        verification_code = request.session.get('verification_code')
        phone = request.session.get('phone')
        expiry = request.session.get('verification_expiry')
        attempts = request.session.get('verification_attempts', 0)

        if not expiry or timezone.now() >= datetime.datetime.fromisoformat(expiry):
            clear_otp_session(request)
            messages.error(request, 'مهلت اعتبار کد تأیید به پایان رسیده است.')
            return redirect('account:otp_request')

        if attempts >= 5:
            clear_otp_session(request)
            messages.error(request, 'تعداد دفعات مجاز تلاش به پایان رسیده است. لطفاً کد جدیدی درخواست کنید.')
            return redirect('account:otp_request')

        if code_match(code, verification_code):
            user = ShopUser.objects.filter(phone=phone).first()
            if not user:
                user = ShopUser.objects.create_user(phone=phone)

            if not user.is_active:
                clear_otp_session(request)
                messages.error(request, 'حساب کاربری شما غیرفعال است.')
                return redirect('account:otp_request')

            login(request, user)
            clear_otp_session(request)
            return redirect('shop:products')

        attempts += 1
        request.session['verification_attempts'] = attempts
        remaining = 5 - attempts
        messages.error(request, f'کد تأیید نامعتبر است. تعداد تلاش‌های باقی‌مانده: {remaining}')

    expiry = request.session.get('verification_expiry')
    remaining_seconds = 0

    if expiry:
        expiry_time = datetime.datetime.fromisoformat(expiry)
        remaining_seconds = max(0, int((expiry_time - timezone.now()).total_seconds()))

    return render(request, 'account/otp_verify.html', {'remaining_seconds': remaining_seconds})