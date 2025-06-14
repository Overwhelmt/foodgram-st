from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from foodgram.constants import (PROFILE_IMAGE_FOLDER, MAX_EMAIL_LENGTH,
                            MAX_FIRSTNAME_LENGTH, MAX_LASTNAME_LENGTH,
                            MAX_LOGIN_LENGTH, LOGIN_REGEX_PATTERN)


class User(AbstractUser):
    AUTH_FIELD = "email"
    REQUIRED_DATA = ["login", "first_name", "last_name"]

    email = models.EmailField(
        verbose_name="Электронная почта",
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
    )
    login = models.CharField(
        verbose_name="Логин",
        max_length=MAX_LOGIN_LENGTH,
        unique=True,
        db_index=True,
        validators=[RegexValidator(regex=LOGIN_REGEX_PATTERN)],
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=MAX_FIRSTNAME_LENGTH,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=MAX_LASTNAME_LENGTH,
    )
    profile_image = models.ImageField(
        verbose_name="Фото профиля",
        upload_to=PROFILE_IMAGE_FOLDER,
        blank=True,
    )

    class Meta:
        verbose_name = "Аккаунт"
        verbose_name_plural = "Аккаунты"
        ordering = ("login",)

    def __str__(self):
        return self.login


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
        ordering = ("author__login",)

    def __str__(self):
        return f"{self.follower} {self.author}"