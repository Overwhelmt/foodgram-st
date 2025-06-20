from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer, TokenCreateSerializer
from rest_framework import serializers

from api.fields import Base64ImageField
from users.models import User, Follow

# ИЗМЕНЕНО: класс переименован для избежания конфликта
class UserReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных пользователя с информацией о подписках."""
    
    # ИЗМЕНЕНО: поле is_following -> is_subscribed
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(use_url=True, required=False, read_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed", # ИЗМЕНЕНО
            "avatar",
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на данного пользователя."""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Follow.objects.filter(follower=request.user, author=obj).exists()


class CustomUserCreateSerializer(DjoserUserCreateSerializer):
    """Сериализатор для создания новых пользователей."""
    
    class Meta(DjoserUserCreateSerializer.Meta):
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )


class SetAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""
    
    avatar = Base64ImageField(use_url=True, required=True)

    class Meta:
        model = User
        fields = ("avatar",)


class CustomTokenCreateSerializer(TokenCreateSerializer):
    def validate(self, attrs):
        attrs['username'] = attrs.get('email')
        return super().validate(attrs)
    

class UserCreateResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name", "last_name")