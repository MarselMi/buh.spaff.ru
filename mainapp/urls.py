from django.urls import path
from .views import MainPageView
from authapp.views import CustomLogoutView, CustomLoginView  #, CreateUserView


urlpatterns = [
    path('', MainPageView.as_view(), name='main_page'),
    path('login/', CustomLoginView.as_view(), name='login'),
    # path('create/', CreateUserView.as_view(), name='create'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]

