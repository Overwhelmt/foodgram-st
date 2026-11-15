from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer as DjoserCreateSerializer
from rest_framework import serializers

from foodgram.fields import Base64ImageField

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is None or not user.is_authenticated or user == obj:
            return False
        return obj.subscribers.filter(user=user).exists()

    def get_avatar(self, obj):
        if not obj.avatar:
            return None
        request = self.context.get('request')
        url = obj.avatar.url
        if request is None:
            return url
        return request.build_absolute_uri(url)


class UserCreateSerializer(DjoserCreateSerializer):
    class Meta(DjoserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        from recipes.serializers import RecipeMinifiedSerializer

        request = self.context.get('request')
        recipes = obj.recipes.all()
        limit = None
        if request is not None:
            limit = request.query_params.get('recipes_limit')
        if limit and str(limit).isdigit():
            recipes = recipes[:int(limit)]
        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data
