from django import forms

from .models import LogisticsOption, Order


class CheckoutForm(forms.ModelForm):
    logistics_option = forms.ModelChoiceField(queryset=LogisticsOption.objects.all(), widget=forms.RadioSelect)

    class Meta:
        model = Order
        fields = ['logistics_option']
