from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import MyUser

UserAdmin.fieldsets += (
    ('Дополнительные поля', {'fields': ('is_subscribed', 'avatar',)}),
)
# Регистрируем модель в админке:
admin.site.register(MyUser, UserAdmin)