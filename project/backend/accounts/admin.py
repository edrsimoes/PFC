from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Preferências", {"fields": ("tema_preferido",)}),
    )
    list_display = ("username", "email", "is_staff", "criado_em")
