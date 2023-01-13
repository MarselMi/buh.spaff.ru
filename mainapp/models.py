from django.db import models
from authapp.models import CustomUser

TRANSACTION_CHOICE = [
    (1, 'Приход'),
    (2, 'Расход'),
]


class PayType(models.Model):
    pay_type = models.CharField(max_length=20, verbose_name='Тип платежа')

    def __str__(self):
        return f'{self.pay_type}'

    class Meta:
        verbose_name = 'Типы платежей'
        verbose_name_plural = 'Тип платежа'
        ordering = ("-pk",)


class BalanceHolder(models.Model):
    holder_name = models.CharField(max_length=65, verbose_name='Наименование')
    holder = models.CharField(max_length=35, verbose_name='Держатель')
    holder_balance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Баланс Держателя')
    deleted = models.BooleanField(default=False, verbose_name='Удалено')

    def __str__(self):
        return f'{self.holder_name} {self.holder}'

    def delete(self, *args, **kwargs):
        self.deleted = True
        self.save()

    class Meta:
        verbose_name = 'Балансодержателя'
        verbose_name_plural = 'Балансодержатели'
        ordering = ("-pk",)


class Transaction(models.Model):
    create_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    update_date = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    type_transaction = models.IntegerField(choices=TRANSACTION_CHOICE, verbose_name='Тип транзакции')
    transaction_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата Транзакции')

    name = models.CharField(max_length=65, verbose_name='Наименование')
    description = models.TextField(verbose_name='Подробнее')
    balance_holder = models.ForeignKey(BalanceHolder, on_delete=models.CASCADE, verbose_name='Балансодержатель')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    type_payment = models.ForeignKey(PayType, on_delete=models.CASCADE, verbose_name='Тип')
    tags = models.TextField(verbose_name='Теги')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Автор')
    deleted = models.BooleanField(default=False, verbose_name='Удален')

    def __str__(self):
        return f'{self.name}'

    def delete(self, *args, **kwargs):
        self.deleted = True
        self.save()

    class Meta:
        verbose_name = 'Транзакции'
        verbose_name_plural = 'Транзакция'
        ordering = ("-pk",)


class AdditionalDataTransaction(models.Model):
    transaction_id = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    notes = models.TextField(verbose_name='Дополнительные данные по транзакции')
    deleted = models.BooleanField(default=False, verbose_name='Удален')

    def __str__(self):
        return f'ID Транзакции - {self.transaction_id}'

    def delete(self, *args, **kwargs):
        self.deleted = True
        self.save()

    class Meta:
        verbose_name = 'Доп. данные по транзакциям'
        verbose_name_plural = 'Доп. данные по транзакции'
        ordering = ("-pk",)