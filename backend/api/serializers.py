from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.fields import Base64ImageField
from users.models import User


class UserReadSerializer(UserCreateSerializer):
    """Сериализатор для чтения данных пользователя с информацией о подписках."""
    
    is_following = serializers.SerializerMethodField()
    avatar = Base64ImageField(use_url=True, required=False)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_following",
            "avatar",
        )
        read_only_fields = ("id", "is_following")

    def get_is_following(self, obj):
        """Проверяет, подписан ли текущий пользователь на данного пользователя."""
        request = self.context.get("request")
        return (
            request and
            request.user.is_authenticated and
            request.user.subscriptions_where_subscriber.filter(author=obj).exists()
        )


class UserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания новых пользователей."""
    
    class Meta(UserReadSerializer.Meta):
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
            "username": {"required": True},
        }


class UserAvatarUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""
    
    avatar = Base64ImageField(use_url=True, required=True)

    class Meta:
        model = User
        fields = ("avatar",)
        extra_kwargs = {"avatar": {"required": True}}

    def validate_avatar(self, value):
        """Валидация загружаемого аватара."""
        if not value:
            raise ValidationError("Необходимо загрузить изображение для аватара")
        return value