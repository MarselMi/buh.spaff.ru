from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from mainapp.models import Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'name',
            'type_transaction',
            'description',
            'balance_holder',
            'amount',
            'type_payment',
            'tags',
        ]

    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Transaction'))