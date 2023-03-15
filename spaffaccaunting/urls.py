from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from apiapp.views import (
    UserModelView, PayTypeModelView, BalanceHolderModelView,
    TransactionModelView, AdditionalDataTransactionModelView,

)


router = DefaultRouter()
router.register('users', UserModelView)
router.register('pay-type', PayTypeModelView)
router.register('balance-holder', BalanceHolderModelView)
router.register('transactions', TransactionModelView)
router.register('additional-data', AdditionalDataTransactionModelView)
router.register('balance-holder', BalanceHolderModelView)
router.register('transactions', TransactionModelView)


urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('__debug__/', include('debug_toolbar.urls')),
    path('', include('mainapp.urls')),
    path('api-v1/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler404 = "mainapp.views.handler404"
handler403 = "mainapp.views.handler403"
handler405 = "mainapp.views.handler405"
handler500 = "mainapp.views.handler500"
handler501 = "mainapp.views.handler501"
