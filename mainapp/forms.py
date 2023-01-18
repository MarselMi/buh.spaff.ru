from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from mainapp.models import Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['name', 'type_transaction', 'description', 'balance_holder', 'amount', 'type_payment', 'tags']
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'transactionName', 'placeholder': 'Имя транзакции'}),
            'type_transaction': forms.Select(
                attrs={'class': 'form-select', 'id': 'transactionType', 'placeholder': 'Тип транзакции'}),
            'description': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'transactionDescription', 'placeholder': 'Описание'}),
            'balance_holder': forms.Select(
                attrs={'class': 'form-select', 'id': 'transactionBalance_holder', 'placeholder': 'Выберите Балансодержателя'}),
            'amount': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'transactionAmount', 'placeholder': 'Сумма транзакции'}),
            'type_payment': forms.Select(
                attrs={'class': 'form-select', 'id': 'transactionPayment', 'placeholder': 'Тип платежа'}),
            'tags': forms.Textarea(
                attrs={'class': 'form-control', 'id': 'transactionTags', 'placeholder': 'Теги для данной транзакции'})
        }

    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Transaction'))