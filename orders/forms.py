from django import forms
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
    phone = PhoneVerificationForm()
    class Meta:
        model = Order
        fields = ('first_name', 'last_name', 'phone', 'address',
                  'postcode', 'province', 'city')
