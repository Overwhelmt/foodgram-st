from django.contrib import admin
from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from .models import User


@register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "id",
        "login",
        "email",
        "first_name",
        "last_name",
        "password",
        "profile_image",
        "recipes_amount",
        "followers_amount",
    )
    list_filter = ("login", "email")
    search_fields = ("login__icontains", "email__icontains")

    @admin.display(description="Авторских рецептов")
    def authored_recipes_amount(self, user_instance):
        return user_instance.recipes.count()

    @admin.display(description="Подписчиков")
    def followers_amount(self, user_instance):
        return user_instance.subscriptions_where_author.count()

    fieldsets = (
        (None, {"fields": ("login", "hashed_password")}),
        ("Персональная информация", {
         "fields": ("given_name", "last_name", "email")}),
        ("Дополнительно", {"fields": ("profile_image",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("login", "email", "password1", "password2"),
        }),
    )