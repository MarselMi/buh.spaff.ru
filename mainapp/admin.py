from django.contrib import admin
from mainapp import models


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
    pass


@admin.register(models.CustomUser)
class AdminCustomUser(admin.ModelAdmin):
    pass

