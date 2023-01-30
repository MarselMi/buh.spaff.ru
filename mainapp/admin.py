from django.contrib import admin

from authapp.forms import CustomUserCreationForm, CustomUserChangeForm
from authapp.models import CustomUser
from mainapp import models
from django.contrib.auth.admin import UserAdmin


@admin.register(models.TransactionLog)
class AdminCrudLogTable(admin.ModelAdmin):
    pass


@admin.register(models.PayType)
class AdminPayType(admin.ModelAdmin):
    pass


@admin.register(models.AdditionalDataTransaction)
class AdminAdditionalDataTransaction(admin.ModelAdmin):
    pass


@admin.register(models.BalanceHolder)
class AdminBalanceHolder(admin.ModelAdmin):
    list_display = ["organization_holder", "name_holder", "holder_balance", "payment_account", "deleted"]


@admin.register(models.Transaction)
class AdminTransaction(admin.ModelAdmin):
    list_display = ['name', 'type_transaction', 'amount', 'create_date', 'transaction_date',
                    'balance_holder', 'author', 'check_img']
    list_per_page = 10
    search_fields = ['tags']


class AdminCustomUser(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['username', 'first_name', 'is_staff']


admin.site.register(CustomUser, AdminCustomUser)

