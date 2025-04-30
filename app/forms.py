# refunds/forms.py
from django import forms
from .models import RefundRequest

class RefundRequestForm(forms.ModelForm):
    class Meta:
        model = RefundRequest
        fields = ['ticket_code', 'reason']
        widgets = {
            'ticket_code': forms.TextInput(attrs={'class': 'form-control'}),
             'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Explicá el motivo'}),
        }   
