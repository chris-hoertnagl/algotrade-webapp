from django import forms
from .models import Algorithm


class AlgorithmForm(forms.ModelForm):
    class Meta:
        model = Algorithm
        fields = ["name", "symbol", "stop_loss", "take_profit", "trade_qty"]


