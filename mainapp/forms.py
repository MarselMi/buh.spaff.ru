from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from mainapp.models import Transaction, BalanceHolder, AdditionalDataTransaction, PayType


class TransactionForm(forms.ModelForm):

    class Meta:

        model = Transaction

        fields = ['name', 'status', 'type_transaction', 'transaction_date', 'description', 'balance_holder',
                  'amount', 'type_payment', 'check_img', 'tags']

        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control mb-2', 'id': 'transactionName', 'placeholder': 'Имя транзакции', 'clean': 'true'}
            ),
            'transaction_date': forms.TextInput(
                attrs={'class': 'form-control mb-2', 'id': 'datepicker', 'placeholder': 'Дата транзакции'}
            ),
            'type_transaction': forms.Select(
                attrs={'class': 'form-select mb-2', 'id': 'transactionType', 'placeholder': 'Тип транзакции'}
            ),
            'description': forms.TextInput(
                attrs={'class': 'form-control mb-2', 'id': 'transactionDescription', 'placeholder': 'Описание'}
            ),
            'balance_holder': forms.Select(
                attrs={'class': 'form-select mb-2', 'id': 'transactionBalance_holder', 'placeholder': 'Выберите Балансодержателя'}
            ),
            'amount': forms.TextInput(
                attrs={'class': 'form-control mb-2', 'id': 'transactionAmount', 'placeholder': 'Сумма транзакции'}
            ),
            'type_payment': forms.Select(
                attrs={'class': 'form-select mb-2', 'id': 'transactionPayment', 'placeholder': 'Тип платежа'}
            ),
            'check_img': forms.FileInput(),
            'tags': forms.Textarea(
                attrs={'class': 'form-control mb-2', 'id': 'transactionTags', 'placeholder': 'Теги для данной транзакции'}
            ),
            'status': forms.Select(
                attrs={'class': 'form-select mb-2', 'id': 'transactionStatus', 'placeholder': 'Статус транзакции'}
            ),
        }

    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Transaction'))


class TransactionUpdateForm(forms.ModelForm):

    class Meta:

        model = Transaction

        fields = ['status', 'transaction_date', 'description',
                  'amount', 'type_payment', 'check_img', 'tags']

        widgets = {
            'status': forms.Select(
                attrs={'class': 'form-select mb-2', 'id': 'transactionStatus', 'placeholder': 'Статус транзакции'}
            ),
            'transaction_date': forms.DateInput(
                attrs={'class': 'form-control mb-2', 'id': 'datepicker', 'placeholder': 'Дата транзакции'}
            ),
            'description': forms.TextInput(
                attrs={'class': 'form-control mb-2', 'id': 'transactionDescription', 'placeholder': 'Описание'}
            ),
            'balance_holder': forms.TextInput(
                attrs={'class': 'form-control mb-2', 'id': 'transactionBalance_holder', 'disabled': 'true'}
            ),
            'amount': forms.TextInput(
                attrs={'class': 'form-control mb-2', 'id': 'transactionAmount', 'placeholder': 'Сумма транзакции'}
            ),
            'type_payment': forms.Select(
                attrs={'class': 'form-select mb-2', 'id': 'transactionPayment', 'placeholder': 'Тип платежа'}
            ),
            'check_img': forms.FileInput(),
            'tags': forms.Textarea(
                attrs={'class': 'form-control mb-2', 'id': 'transactionTags', 'placeholder': 'Теги для данной транзакции'}
            ),
        }

    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Transaction'))


class BalanceHolderForm(forms.ModelForm):
    class Meta:
        model = BalanceHolder
        fields = ['holder_name', 'holder', 'holder_balance']
        widgets = {
            'holder_name': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'HolderName', 'placeholder': 'Наименование организации'}
            ),
            'holder': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'Holder', 'placeholder': 'Имя балансодержателя'}
            ),
            'holder_balance': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'HolderBalance', 'placeholder': 'Баланс'}
            ),
        }

    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save BalanceHolder'))


class AdditionalDataTransactionForm(forms.ModelForm):

    class Meta:
        model = AdditionalDataTransaction
        fields = ['transaction_id', 'notes']
        widgets = {
            'transaction_id': forms.Select(
                attrs={'class': 'form-select', 'id': 'TransactionID', 'selected': "Выберите транзакцию"}
            ),
            'notes': forms.Textarea(
                attrs={'class': 'form-control', 'id': 'TransactionNotes', 'placeholder': 'Введите дополнительные данные по выбранной транзакции'}
            )
        }

    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['transaction_id'] = ('', 'Выберите транзакцию')
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save AdditionalDataTransaction'))


class PayTypeForm(forms.ModelForm):
    class Meta:
        model = PayType
        fields = ['pay_type']
        widgets = {
            'pay_type': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'PayType', 'placeholder': 'Введите тип платежа'}
            )
        }

    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save PayType'))
