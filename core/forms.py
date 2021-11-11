from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from .models import Document, Item, CATEGORY_CHOICES


PAYMENT_CHOICES = (
    ('S', 'Stripe'),
)


class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    shipping_country = CountryField(blank_label='(select country)').formfield(
        required=False,
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100',
        }))
    shipping_zip = forms.CharField(required=False)

    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_country = CountryField(blank_label='(select country)').formfield(
        required=False,
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100',
        }))
    billing_zip = forms.CharField(required=False)

    same_billing_address = forms.BooleanField(required=False)
    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)

    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT_CHOICES)


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria-label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))


class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 4
    }))
    email = forms.EmailField()


class PaymentForm(forms.Form):
    stripeToken = forms.CharField(required=False)
    save = forms.BooleanField(required=False)
    use_default = forms.BooleanField(required=False)


class NewItemForm(forms.ModelForm):
    class Meta:
        model=Item
        fields=['title','price','discount_price','category','description','image','image2']
        widgets={
            'title': forms.TextInput(attrs={'class': 'form-desc', 'style':'border:1px solid gray; border-radius:10px'}),
            'price': forms.TextInput(attrs={'class': 'form-desc', 'style':'border:1px solid gray; border-radius:10px'}),
            'discount_price': forms.TextInput(attrs={'class': 'form-desc', 'style':'border:1px solid gray; border-radius:10px'}),
            'category': forms.Select(choices=CATEGORY_CHOICES, attrs={'class': 'form-desc', 'style':'border:1px solid gray; border-radius:10px'}),
            'description': forms.Textarea(attrs={'class': 'form-desc', 'style':'border:1px solid gray; border-radius:10px'}),
            'image': forms.FileInput(attrs={'class': 'form-desc', 'style':'border:1px solid gray; border-radius:10px'}),
            'image2': forms.FileInput(attrs={'class': 'form-desc', 'style':'border:1px solid gray; border-radius:10px'}),
        }


class SignUpForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username',
        'aria-label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))
    email = forms.EmailField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email',
        'aria-label': 'Recipient\'s username', 
        'aria-describedby': 'basic-addon2'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password',
        'aria-label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username',
        'aria-label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password',
        'aria-label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['description', 'document']
        widgets = {
            'description':forms.TextInput(attrs={'class': 'form-desc', 'style':'border:1px solid gray; border-radius:10px'}), 
            'document':forms.FileInput(attrs={'class': 'doc-input', 'style':'font-size:14px'})
            }