from django import forms
from .models import Order

class CheckoutForm(forms.ModelForm):
    PAYMENT_CHOICES = [
        ('credit_card', 'Credit / Debit Card (Instant Simulation)'),
        ('upi', 'UPI / QR Payment (Instant Simulation)'),
        ('paypal', 'PayPal (Instant Simulation)'),
        ('cod', 'Cash on Delivery (Pay on arrival)'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'payment-radio'})
    )

    class Meta:
        model = Order
        fields = [
            'full_name', 'email', 'phone',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'payment_method', 'notes'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone Number'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Street Address'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Apt, Suite, Unit (optional)'}),
            'city': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'State / Province'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Postal / ZIP Code'}),
            'country': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Country'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Delivery notes / instructions (optional)'}),
        }
