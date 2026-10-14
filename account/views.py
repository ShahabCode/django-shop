from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import ShopUserCreationForm, AddressForm
from .models import Address


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


@login_required()
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