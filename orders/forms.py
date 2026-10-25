from django import forms

from account.models import Address
from .models import Order

class PhoneVerificationForm(forms.Form):
    phone = forms.CharField(label='شماره موبایل', max_length=11)

    def clean_phone(self):
        phone = self.cleaned_data['phone']

        if not phone.isdigit():
            raise forms.ValidationError('شماره موبایل باید فقط شامل اعداد باشد.')

        if len(phone) != 11 or not phone.startswith('09'):
            raise forms.ValidationError('شماره موبایل باید ۱۱ رقم باشد و با 09 شروع شود.')

        return phone


class OrderCreateForm(forms.ModelForm):
    phone = forms.CharField(
        label='شماره موبایل',
        max_length=11,
    )

    saved_address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        label='آدرس‌های ذخیره‌شده',
        required=False,
        empty_label='آدرس جدید وارد می‌کنم',
    )

    class Meta:
        model = Order
        fields = (
            'first_name',
            'last_name',
            'phone',
            'address',
            'postcode',
            'province',
            'city',
        )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user

        if user is not None:
            self.fields['saved_address'].queryset = (
                Address.objects.filter(user=user)
            )

        for field_name in ('address', 'postcode', 'province', 'city'):
            self.fields[field_name].required = False

    def clean_phone(self):
        phone = self.cleaned_data['phone']

        if not phone.isdigit():
            raise forms.ValidationError(
                'شماره موبایل باید فقط شامل اعداد باشد.'
            )

        if len(phone) != 11 or not phone.startswith('09'):
            raise forms.ValidationError(
                'شماره موبایل باید ۱۱ رقم باشد و با 09 شروع شود.'
            )

        return phone

    def clean(self):
        cleaned_data = super().clean()
        saved_address = cleaned_data.get('saved_address')

        if saved_address:
            cleaned_data['address'] = saved_address.address
            cleaned_data['postcode'] = saved_address.postal_code
            cleaned_data['province'] = saved_address.province
            cleaned_data['city'] = saved_address.city
        else:
            required_fields = (
                'address',
                'postcode',
                'province',
                'city',
            )

            for field_name in required_fields:
                if not cleaned_data.get(field_name):
                    self.add_error(
                        field_name,
                        'این فیلد الزامی است.'
                    )

        return cleaned_data


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('status',)