from django.db import models
from django.contrib.auth.models import AbstractBaseUser, UserManager, PermissionsMixin
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    pass

    def __str__(self):
        return self.username



# class CustomUser(AbstractBaseUser, PermissionsMixin):
#
#     username = models.CharField(max_length=20, blank=True, unique=True, verbose_name='Логин')
#     email = models.EmailField(blank=True, unique=True, verbose_name="Email")
#     telephone_number = models.CharField(max_length=12, unique=True, verbose_name='Номер Телефона')
#     first_name = models.CharField(max_length=25, verbose_name="Имя")
#     last_name = models.CharField(max_length=25, verbose_name="Фамилия")
#     is_staff = models.BooleanField(default=False, verbose_name='Персонал')
#     is_active = models.BooleanField(default=True)
#
#     objects = UserManager()
#
#     USERNAME_FIELD = 'username'
#
#     REQUIRED_FIELDS = [
#         'telephone_number',
#         'first_name',
#         'last_name'
#     ]
#
#     def __str__(self):
#         return f'{self.last_name} {self.first_name}'
#
#     class Meta:
#         verbose_name = 'Пользователь'
#         verbose_name_plural = 'Пользователи'
#         ordering = ("-pk",)