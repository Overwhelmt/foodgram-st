from rest_framework import serializers

from api.fields import Base64ImageField
from api.serializers import UserProfileSerializer
from foodgram.constants import INGREDIENT_RECIPE_MIN_AMOUNT
from recipes.models import (FavoriteRecipe, Ingredient, RecipeIngredient, Dish,
                          ShoppingList)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")
    name = serializers.CharField(source="ingredient.title")
    measurement_unit = serializers.CharField(source="ingredient.unit")
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class BasicIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор информации об ингредиенте"""
    
    class Meta:
        model = Ingredient
        fields = ("id", "title", "unit")


class DishDetailSerializer(serializers.ModelSerializer):
    chef = UserProfileSerializer()
    composition = RecipeIngredientSerializer(many=True)
    is_favorite = serializers.SerializerMethodField()
    in_shopping_list = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = (
            "id",
            "chef",
            "composition",
            "is_favorite",
            "in_shopping_list",
            "title",
            "photo",
            "instructions",
            "cooking_duration",
        )

    def get_is_favorite(self, obj):
        request = self.context.get("request")
        return (
            request and 
            request.user.is_authenticated and
            request.user.favorited_by.filter(dish=obj).exists()
        )

    def get_in_shopping_list(self, obj):
        request = self.context.get("request")
        return (
            request and 
            request.user.is_authenticated and
            request.user.in_shopping_lists.filter(dish=obj).exists()
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


class DishCreateUpdateSerializer(serializers.ModelSerializer):
    composition = IngredientAmountSerializer(many=True)
    photo = Base64ImageField(use_url=True)

    class Meta:
        model = Dish
        fields = (
            "composition",
            "title",
            "photo",
            "instructions",
            "cooking_duration",
        )

    def to_representation(self, instance):
        return DishDetailSerializer(
            instance,
            context={"request": self.context.get("request")}
        ).data

    def validate(self, data):
        ingredients = data.get("composition", [])
        
        if not ingredients:
            raise serializers.ValidationError(
                "Необходимо указать хотя бы один ингредиент"
            )

        ids = [item["id"] for item in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                "Ингредиенты должны быть уникальными"
            )

        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop("composition")
        dish = Dish.objects.create(
            **validated_data,
            chef=self.context["request"].user
        )
        self._create_ingredients(dish, ingredients_data)
        return dish

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        self._create_ingredients(
            instance,
            validated_data.pop("composition")
        )
        return super().update(instance, validated_data)

    def _create_ingredients(self, dish, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                dish=dish,
                ingredient_id=item["id"],
                quantity=item["amount"]
            )
            for item in ingredients_data
        ])


class DishShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = ("id", "title", "photo", "cooking_duration")


class BaseUserDishRelationSerializer:
    class Meta:
        fields = ("user", "dish")

    def to_representation(self, instance):
        return DishShortSerializer(instance.dish).data

    def _validate_relation(self, data, relation_name):
        if data["user"].get_queryset().filter(
            dish=data["dish"]
        ).exists():
            raise serializers.ValidationError(
                f"Рецепт уже добавлен в {relation_name}"
            )
        return data


class FavoriteSerializer(
    BaseUserDishRelationSerializer,
    serializers.ModelSerializer
):
    class Meta(BaseUserDishRelationSerializer.Meta):
        model = FavoriteRecipe

    def validate(self, data):
        return self._validate_relation(data, "избранное")


class ShoppingListSerializer(
    BaseUserDishRelationSerializer,
    serializers.ModelSerializer
):
    class Meta(BaseUserDishRelationSerializer.Meta):
        model = ShoppingList

    def validate(self, data):
        return self._validate_relation(data, "список покупок")