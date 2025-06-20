# recipes/serializers.py

from rest_framework import serializers

from api.fields import Base64ImageField
from api.serializers import UserReadSerializer
from foodgram.constants import INGREDIENT_RECIPE_MIN_AMOUNT
from recipes.models import (FavoriteRecipe, Ingredient, RecipeIngredient, Recipe,
                            ShoppingList)


class BasicIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор информации об ингредиенте"""

    class Meta:
        model = Ingredient
        # ИЗМЕНЕНО: 'unit' -> 'measurement_unit'
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', # ИЗМЕНЕНО: 'ingredient.unit' -> 'ingredient.measurement_unit'
        read_only=True
    )
    # ИЗМЕНЕНО: source убран, т.к. имя поля в модели 'amount'
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserReadSerializer(read_only=True)
    # ИЗМЕНЕНО: source указывает на новый related_name
    ingredients = RecipeIngredientSerializer(many=True, source='ingredients_in_recipe')
    # ИЗМЕНЕНО: Поля is_favorite и in_shopping_list переименованы
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        # ИЗМЕНЕНО: Поля приведены в соответствие со спецификацией
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        return (
            request and
            request.user.is_authenticated and
            FavoriteRecipe.objects.filter(user=request.user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        return (
            request and
            request.user.is_authenticated and
            ShoppingList.objects.filter(user=request.user, recipe=obj).exists()
        )


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ("id", "amount")

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f"Ингредиент с ID {value} не найден"
            )
        return value

    def validate_amount(self, value):
        if value < INGREDIENT_RECIPE_MIN_AMOUNT:
            raise serializers.ValidationError(
                f"Минимальное количество: {INGREDIENT_RECIPE_MIN_AMOUNT}"
            )
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    # ИЗМЕНЕНО: Поля переименованы для соответствия спецификации
    ingredients = IngredientAmountSerializer(many=True)
    image = Base64ImageField(use_url=True)
    
    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "image",
            "name",
            "text",
            "cooking_time",
        )

    def to_representation(self, instance):
        # Используем RecipeListSerializer для вывода данных после создания/обновления
        return RecipeListSerializer(
            instance,
            context={"request": self.context.get("request")}
        ).data

    def validate(self, data):
        ingredients = data.get("ingredients", [])
        if not ingredients:
            raise serializers.ValidationError(
                {"ingredients": "Необходимо указать хотя бы один ингредиент."}
            )

        ids = [item["id"] for item in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                {"ingredients": "Ингредиенты должны быть уникальными."}
            )
        return data

    def _create_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item["id"],
                amount=item["amount"]
            )
            for item in ingredients_data
        ])

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(
            **validated_data,
            author=self.context["request"].user
        )
        self._create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        # Очищаем старые ингредиенты только если они есть в запросе
        if "ingredients" in validated_data:
            ingredients_data = validated_data.pop("ingredients")
            instance.ingredients_in_recipe.all().delete()
            self._create_ingredients(instance, ingredients_data)
        
        return super().update(instance, validated_data)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        # ИЗМЕНЕНО: Поля переименованы для соответствия схеме RecipeMinified
        fields = ("id", "name", "image", "cooking_time")


class BaseUserRecipeRelationSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
        fields = ("user", "recipe")

    def to_representation(self, instance):
        # Используем RecipeMinifiedSerializer для представления данных
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data

    def _validate_relation(self, Model, data, error_message):
        if Model.objects.filter(user=data["user"], recipe=data["recipe"]).exists():
            raise serializers.ValidationError({"errors": error_message})
        return data


class FavoriteSerializer(BaseUserRecipeRelationSerializer):
    class Meta(BaseUserRecipeRelationSerializer.Meta):
        model = FavoriteRecipe

    def validate(self, data):
        return self._validate_relation(
            FavoriteRecipe, data, "Рецепт уже есть в избранном."
        )


class ShoppingListSerializer(BaseUserRecipeRelationSerializer):
    class Meta(BaseUserRecipeRelationSerializer.Meta):
        model = ShoppingList

    def validate(self, data):
        return self._validate_relation(
            ShoppingList, data, "Рецепт уже есть в списке покупок."
        )