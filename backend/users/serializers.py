from rest_framework import serializers

from api.serializers import UserProfileSerializer
from recipes.serializers import ShortRecipeSerializer
from users.models import Follow


class FollowSerializer(UserProfileSerializer):
    recipes = serializers.SerializerMethodField(method_name="get_recipes")
    recipes_amount = serializers.ReadOnlyField(source="recipes.count", read_only=True)

    class Meta(UserProfileSerializer.Meta):
        fields = (*UserProfileSerializer.Meta.fields, 'recipes', 'recipes_amount')

    def get_recipes(self, obj):
        ctx = self.context['request']
        queryset = obj.recipes.all()
        limit_param = ctx.query_params.get('recipes_limit')

        if limit_param and limit_param.isdigit():
            queryset = queryset[:int(limit_param)]
        
        return ShortRecipeSerializer(
            queryset,
            context={'request': ctx},
            many=True
        ).data


class FollowCreateSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_amount = serializers.SerializerMethodField()

    class Meta:
            model = Follow
            fields = ('author', 'follower', 'recipes', 'recipes_amount')
            write_only_fields = ('author', 'follower')

    def get_cooking_items(self, sub_obj):
        return ShortRecipeSerializer(
            sub_obj.author.recipes.all(),
            context=self.context,
            many=True
        ).data
    
    def get_items_total(self, sub_obj):
        return sub_obj.author.recipes.count()

    def to_representation(self, sub_instance):
        author_data = UserProfileSerializer(
            sub_instance.author,
            context=self.context
        ).data
        
        return {
            **author_data,
            **super().to_representation(sub_instance)
        }
    
    def validate(self, attrs):
        if attrs['follower'].id == attrs['author'].id:
            raise serializers.ValidationError(
                {'author': 'Нельзя быть подписанным на себя'}
            )
        return attrs