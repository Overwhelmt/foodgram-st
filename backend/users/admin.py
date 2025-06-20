from django.contrib import admin
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from .models import User


@register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "password",
        "avatar",
        "authored_recipes_amount",
        "followers_amount",
    )
    list_filter = ("username", "email")
    search_fields = ("username__icontains", "email__icontains")

    @admin.display(description="Авторских рецептов")
    def authored_recipes_amount(self, user_instance):
        return user_instance.authored_recipes.count()

    @admin.display(description="Подписчиков")
    def followers_amount(self, user_instance):
        return user_instance.creator_subscriptions.count()

    fieldsets = (
        (None, {"fields": ("username", "hashed_password")}),
        ("Персональная информация", {
         "fields": ("first_name", "last_name", "email")}),
        ("Дополнительно", {"fields": ("avatar",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2"),
        }),
    )