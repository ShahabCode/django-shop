from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import ShopUser, Address


class BootstrapFormMixin:
    """به همه‌ی ویجت‌های فرم کلاس Bootstrap می‌ده (در __init__ فرم اجرا می‌شه)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                css = 'form-check-input'
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = 'form-select'
            else:
                css = 'form-control'

            widget.attrs['class'] = f"{widget.attrs.get('class', '')} {css}".strip()

            if name == 'phone':
                widget.attrs.update({
                    'dir': 'ltr',
                    'inputmode': 'numeric',
                    'maxlength': 11,
                    'placeholder': '09123456789',
                    'autocomplete': 'tel',
                })
            elif name in ('postal_code', 'postcode'):
                widget.attrs.update({
                    'dir': 'ltr',
                    'inputmode': 'numeric',
                    'maxlength': 10,
                })


class PhoneValidationMixin:
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')

        if not phone.isdigit():
            raise forms.ValidationError('شماره موبایل باید فقط شامل اعداد باشد.')

        if len(phone) != 11 or not phone.startswith('09'):
            raise forms.ValidationError('شماره موبایل باید ۱۱ رقم باشد و با 09 شروع شود.')

        qs = ShopUser.objects.filter(phone=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError('این شماره موبایل قبلاً ثبت شده است.')

        return phone


class ShopUserCreationForm(BootstrapFormMixin, PhoneValidationMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = ShopUser
        fields = ['phone', 'first_name', 'last_name']
        labels = {
            'phone': 'شماره موبایل',
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'رمز عبور'
        self.fields['password2'].label = 'تکرار رمز عبور'
        self.fields['password2'].help_text = 'برای تأیید، رمز عبور را دوباره وارد کنید.'


class ShopUserChangeForm(PhoneValidationMixin, UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = ShopUser
        fields = ['phone', 'first_name', 'last_name',
                  'is_staff', 'is_active', 'is_superuser']


class AddressForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Address
        fields = ['title', 'province', 'city', 'address', 'postal_code', 'is_default']
        labels = {
            'title': 'عنوان آدرس',
            'province': 'استان',
            'city': 'شهر',
            'address': 'نشانی کامل',
            'postal_code': 'کد پستی',
            'is_default': 'به‌عنوان آدرس پیش‌فرض ذخیره شود',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'مثلاً: خانه'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_postal_code(self):
        postal_code = self.cleaned_data['postal_code']

        if not postal_code.isdigit() or len(postal_code) != 10:
            raise forms.ValidationError('کد پستی باید ۱۰ رقم و فقط شامل اعداد باشد.')

        return postal_code
