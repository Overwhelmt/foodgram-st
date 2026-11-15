from django.db import transaction
from rest_framework import serializers

from foodgram.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, RecipeIngredient
from users.serializers import UserSerializer


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(min_value=1)


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )
    image = Base64ImageField()
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True, allow_empty=False)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=256)
    text = serializers.CharField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        errors = {}
        initial = self.initial_data
        required = ('ingredients', 'name', 'text', 'cooking_time')
        if self.instance is None:
            required = required + ('image',)
        for field in required:
            if field not in initial:
                errors[field] = ['Обязательное поле.']
        ingredients = initial.get('ingredients')
        if 'ingredients' in initial and not ingredients:
            errors['ingredients'] = ['Добавьте хотя бы один ингредиент.']
        if 'image' in initial and not initial.get('image'):
            errors['image'] = ['Это поле не может быть пустым.']
        if 'name' in initial and initial.get('name') == '':
            errors['name'] = ['Это поле не может быть пустым.']
        if 'text' in initial and initial.get('text') == '':
            errors['text'] = ['Это поле не может быть пустым.']
        parsed = data.get('ingredients')
        if parsed:
            ids = [item['id'].pk for item in parsed]
            if len(ids) != len(set(ids)):
                errors['ingredients'] = ['Ингредиенты не должны повторяться.']
        if errors:
            raise serializers.ValidationError(errors)
        return data

    def _set_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount'],
            )
            for item in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self._set_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        instance = super().update(instance, validated_data)
        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            self._set_ingredients(instance, ingredients)
        return instance

    def to_representation(self, instance):
        from recipes.querysets import recipe_queryset

        user = self.context['request'].user
        instance = recipe_queryset(user).get(pk=instance.pk)
        return RecipeReadSerializer(instance, context=self.context).data
