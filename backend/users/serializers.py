from rest_framework import serializers

from api.serializers import UserReadSerializer
from recipes.serializers import RecipeMinifiedSerializer
from users.models import Follow


class UserWithRecipesSerializer(UserReadSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count", read_only=True)

    class Meta(UserReadSerializer.Meta):
        fields = (*UserReadSerializer.Meta.fields, 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        queryset = obj.recipes.all()

        if recipes_limit and recipes_limit.isdigit():
            queryset = queryset[:int(recipes_limit)]
        
        return RecipeMinifiedSerializer(
            queryset,
            context={'request': request},
            many=True
        ).data


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('author', 'follower')

    def to_representation(self, instance):
        # Возвращаем данные в формате UserWithRecipesSerializer
        return UserWithRecipesSerializer(
            instance.author,
            context=self.context
        ).data
    
    def validate(self, attrs):
        follower = attrs['follower']
        author = attrs['author']
        if follower == author:
            raise serializers.ValidationError('Нельзя подписаться на самого себя.')
        if Follow.objects.filter(follower=follower, author=author).exists():
            raise serializers.ValidationError('Вы уже подписаны на этого пользователя.')
        return attrs