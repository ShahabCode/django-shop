from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import ShopUser, Address


class PhoneValidationMixin:
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')

        qs = ShopUser.objects.filter(phone=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError('Phone number already taken')

        if not phone.isdigit():
            raise forms.ValidationError('Phone number must be digits')

        if not phone.startswith('09'):
            raise forms.ValidationError('Phone number must start with 09')

        if len(phone) != 11:
            raise forms.ValidationError('Phone number must be 11 digits')

        return phone


class ShopUserCreationForm(PhoneValidationMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = ShopUser
        fields = ['phone', 'first_name', 'last_name']


class ShopUserChangeForm(PhoneValidationMixin, UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = ShopUser
        fields = ['phone', 'first_name', 'last_name',
                  'is_staff', 'is_active', 'is_superuser']

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['title', 'province', 'city', 'address', 'postal_code', 'is_default']