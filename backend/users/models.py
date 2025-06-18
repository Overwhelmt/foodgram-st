from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator
from django.db import models

from foodgram.constants import (USER_AVATAR_STORAGE_PATH, USER_EMAIL_MAX_LEN,
                            USER_FIRST_NAME_MAX_LEN, USER_LAST_NAME_MAX_LEN,
                            USER_USERNAME_MAX_LEN, USERNAME_VALIDATION_REGEX)


class User(AbstractUser):

    email = models.EmailField(
        verbose_name="Электронная почта",
        max_length=USER_EMAIL_MAX_LEN,
        unique=True,
    )
    username = models.CharField(
        verbose_name="Логин",
        max_length=USER_USERNAME_MAX_LEN,
        unique=True,
        db_index=True,
        validators=[RegexValidator(regex=USERNAME_VALIDATION_REGEX)],
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=USER_FIRST_NAME_MAX_LEN,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=USER_LAST_NAME_MAX_LEN,
    )
    profile_image = models.ImageField(
        verbose_name="Фото профиля",
        upload_to=USER_AVATAR_STORAGE_PATH,
        blank=True,
    )
    groups = models.ManyToManyField(
        Group,
        verbose_name='Группы',
        blank=True,
        related_name="custom_user_set",  
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name="custom_user_permissions_set",
        help_text='Specific permissions for this user.',
    )

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"
        ordering = ("username",)

    def __str__(self):
        return self.username


class Follow(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="creator_subscriptions",
        verbose_name="Автор контента",
    )
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_subscriptions",
        verbose_name="Подписчик",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "author"],
                name="no_duplicate_follows"
            )
        ]
        ordering = ("author__username",)

    def __str__(self):
        return f"{self.follower} {self.author}"