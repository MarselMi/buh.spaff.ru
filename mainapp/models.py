from django.db import models
from django.contrib.auth.models import AbstractUser


ACTION_CREATE = 'create'
ACTION_UPDATE = 'update'
ACTION_DELETE = 'delete'

TRANSACTION_CHOICE = [
    ('COMING', 'Приход'),
    ('EXPENDITURE', 'Расход'),
]

STATUS_CHOICES = [
        ('INPROCESS', 'В процессе'),
        ('REJECT', 'Отклонен'),
        ('SUCCESSFULLY', 'Успешно')
    ]

HOLDER_ROLE = [
    ('PRIVATE_PERSONE', 'Частное лицо'),
    ('ORGANISATION', ' Организация')
]


class PayType(models.Model):
    pay_type = models.CharField(unique=True, max_length=60, verbose_name='Тип платежа')

    def __str__(self):
        return f'{self.pay_type}'

    class Meta:
        verbose_name = 'Тип платежа'
        verbose_name_plural = 'Типы платежей'


class BalanceHolder(models.Model):
    holder_type = models.CharField(blank=True, null=True, max_length=20, choices=HOLDER_ROLE, verbose_name='Тип балансодержателя')
    organization_holder = models.CharField(blank=True, null=True, max_length=65, verbose_name='Наименование организации')
    alias_holder = models.CharField(blank=True, null=True, default=None, max_length=35, verbose_name='Псевдоним')
    holder_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Баланс Держателя')
    payment_account = models.CharField(max_length=20, verbose_name='Расчетный счет')
    deleted = models.BooleanField(default=False, verbose_name='Удалено')

    def __str__(self):
        return f'{self.organization_holder}'

    def delete(self, *args, **kwargs):
        self.deleted = True
        self.save()

    class Meta:
        verbose_name = 'Балансодержателя'
        verbose_name_plural = 'Балансодержатели'


class CustomUser(AbstractUser, models.Model):

    available_holders = models.ManyToManyField(BalanceHolder)

    def __str__(self):
        return f'{self.username}'

    class Meta:
        verbose_name = 'Пользователя'
        verbose_name_plural = 'Пользователи'
        ordering = ("-pk",)


class Transaction(models.Model):

    create_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    update_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата изменения')

    type_transaction = models.CharField(max_length=15, choices=TRANSACTION_CHOICE, verbose_name='Тип транзакции')
    transaction_date = models.DateField(verbose_name='Дата Транзакции')

    name = models.CharField(max_length=65, verbose_name='Наименование')
    description = models.TextField(blank=True, null=True, default=None, verbose_name='Подробнее')
    balance_holder = models.ForeignKey(BalanceHolder, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='transaction_balanceholder', verbose_name='Балансодержатель')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    type_payment = models.ForeignKey(PayType, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='transaction_paytype', verbose_name='Тип')
    tags = models.TextField(blank=True, null=True, default=None, verbose_name='Теги')
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='transaction_customuser', verbose_name='Автор')
    check_img = models.FileField(blank=True, null=True, upload_to='img/', verbose_name='Чек')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_CHOICES[2][0], verbose_name='Статус')
    deleted = models.BooleanField(default=False, verbose_name='Удален')

    def __str__(self):
        return f'{self.pk}'

    def delete(self, *args, **kwargs):
        self.deleted = True
        self.save()

    class Meta:
        verbose_name = 'Транзакцию'
        verbose_name_plural = 'Транзакции'


class AdditionalDataTransaction(models.Model):
    transaction_id = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='additionaldatatransaction_transaction', verbose_name='Транзакция')
    notes = models.TextField(verbose_name='Дополнительные данные по транзакции')
    deleted = models.BooleanField(default=False, verbose_name='Удален')

    def __str__(self):
        return f'{self.pk}'

    def delete(self, *args, **kwargs):
        self.deleted = True
        self.save()

    class Meta:
        verbose_name = 'Доп. данные по транзакциям'
        verbose_name_plural = 'Доп. данные по транзакции'


class TransactionLog(models.Model):

    transaction_id = models.IntegerField(verbose_name='ID транзакции')
    changed = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')
    author_references = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='transactionlog_customuser', verbose_name='Автор изменения')

    status = models.CharField(max_length=30, blank=True, null=True, verbose_name='Статус транз до/после')
    transaction_date = models.CharField(max_length=30, blank=True, null=True, verbose_name='Дата транз до/после')
    amount = models.CharField(max_length=30, blank=True, null=True, verbose_name='Сумма транз до/после')
    description = models.TextField(blank=True, null=True, verbose_name='Описание транз до/после')
    type_payment = models.CharField(max_length=25, blank=True, null=True, verbose_name='Тип платежа до/после')
    check_img = models.TextField(blank=True, null=True, verbose_name='Чеки транз до/после')

    class Meta:
        verbose_name = 'Внесенные изменения'
        verbose_name_plural = 'Таблица изменения данных'
