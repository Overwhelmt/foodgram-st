# recipes/models.py

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from foodgram.constants import (INGREDIENT_TITLE_MAX_LEN,
                                INGREDIENT_MIN_QUANTITY,
                                INGREDIENT_MEASUREMENT_MAX_LEN,
                                RECIPE_IMAGE_STORAGE_PATH,
                                RECIPE_MIN_PREP_MINUTES,
                                RECIPE_TITLE_MAX_LEN)

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        max_length=INGREDIENT_MEASUREMENT_MAX_LEN,
        verbose_name="Название продукта",
    )
    measurement_unit = models.CharField(
        max_length=INGREDIENT_TITLE_MAX_LEN,
        verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient"
            )
        ]
        ordering = ("-name",)

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        # ИЗМЕНЕНО: related_name изменен с 'composition' на 'ingredients' для соответствия спецификации API
        related_name="ingredients_in_recipe",
        verbose_name="Блюдо"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="used_in",
        verbose_name="Ингредиент"
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=[MinValueValidator(INGREDIENT_MIN_QUANTITY)]
    )

    class Meta:
        verbose_name = "Состав рецепта"
        verbose_name_plural = "Состав рецептов"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient_pair"
            )
        ]
        ordering = ("recipe__name",)

    def __str__(self):
        return f"{self.recipe} {self.ingredient.measurement_unit} {self.ingredient.name}"


class BaseUserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        verbose_name="Рецепт"
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="%(class)s_no_duplicate_relations"
            )
        ]

    def __str__(self):
        return f"{self.user} {self.recipe}"


class FavoriteRecipe(BaseUserRecipeRelation):
    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        default_related_name = "favorited_by"


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes", # ИЗМЕНЕНО: authored_recipes -> recipes
        verbose_name="Автор"
    )
    name = models.CharField(
        max_length=RECIPE_TITLE_MAX_LEN,
        verbose_name="Название блюда"
    )
    image = models.ImageField(
        upload_to=RECIPE_IMAGE_STORAGE_PATH,
        verbose_name="Фотография",
        blank=True
    )
    text = models.TextField(verbose_name="Инструкция приготовления")
    ingredients = models.ManyToManyField(
        Ingredient,
        # ИЗМЕНЕНО: source для M2M теперь 'RecipeIngredient'
        through='RecipeIngredient',
        verbose_name="Ингредиенты"
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время готовки (мин)",
        validators=[MinValueValidator(RECIPE_MIN_PREP_MINUTES)]
    )
    publication_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Дата публикации"
    )
    favorites = models.ManyToManyField(
        User,
        through=FavoriteRecipe,
        related_name="favorite_recipes",
        verbose_name="Избранное"
    )

    class Meta:
        verbose_name = "Кулинарный рецепт"
        verbose_name_plural = "Кулинарные рецепты"
        ordering = ("-publication_date",)
        default_related_name = "recipes"

    def __str__(self):
        return f"{self.name} от {self.author}"


class ShoppingList(BaseUserRecipeRelation):
    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        # ИЗМЕНЕНО: default_related_name изменен для соответствия с фильтрами и логикой
        default_related_name = "shopping_cart_items"