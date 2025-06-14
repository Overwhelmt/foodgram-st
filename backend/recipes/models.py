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
    title = models.CharField(
        max_length=INGREDIENT_MEASUREMENT_MAX_LEN,
        verbose_name="Название продукта",
        db_index=True
    )
    unit = models.CharField(
        max_length=INGREDIENT_TITLE_MAX_LEN,
        verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["title", "unit"],
                name="no_duplicate_ingredients"
            )
        ]
        ordering = ("title",)

    def __str__(self):
        return f"{self.title} ({self.unit})"


class RecipeIngredient(models.Model):
    dish = models.ForeignKey(
        "Dish",
        on_delete=models.CASCADE,
        related_name="composition",
        verbose_name="Блюдо"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="used_in",
        verbose_name="Ингредиент"
    )
    quantity = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=[MinValueValidator(INGREDIENT_MIN_QUANTITY)]
    )

    class Meta:
        verbose_name = "Состав рецепта"
        verbose_name_plural = "Состав рецептов"
        constraints = [
            models.UniqueConstraint(
                fields=["dish", "ingredient"],
                name="unique_recipe_ingredient_pair"
            )
        ]

    def __str__(self):
        return f"{self.quantity} {self.ingredient.unit} {self.ingredient.title}"


class Dish(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="authored_dishes",
        verbose_name="Автор"
    )
    title = models.CharField(
        max_length=RECIPE_TITLE_MAX_LEN,
        verbose_name="Название блюда"
    )
    photo = models.ImageField(
        upload_to=RECIPE_IMAGE_STORAGE_PATH,
        verbose_name="Фотография",
        blank=True
    )
    instructions = models.TextField(verbose_name="Инструкция приготовления")
    components = models.ManyToManyField(
        Ingredient,
        through=RecipeIngredient,
        verbose_name="Ингредиенты"
    )
    cooking_duration = models.PositiveSmallIntegerField(
        verbose_name="Время готовки (мин)",
        validators=[MinValueValidator(RECIPE_MIN_PREP_MINUTES)]
    )
    publication_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Дата публикации"
    )

    class Meta:
        verbose_name = "Кулинарный рецепт"
        verbose_name_plural = "Кулинарные рецепты"
        ordering = ("-publication_date",)
        default_related_name = "dishes"

    def __str__(self):
        return f"{self.title} от {self.author}"


class BaseUserDishRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        verbose_name="Рецепт"
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "dish"],
                name="%(class)s_no_duplicate_relations"
            )
        ]

    def __str__(self):
        return f"{self.user} ↔ {self.dish}"


class FavoriteRecipe(BaseUserDishRelation):
    class Meta(BaseUserDishRelation.Meta):
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        default_related_name = "favorited_by"


class ShoppingList(BaseUserDishRelation):
    class Meta(BaseUserDishRelation.Meta):
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        default_related_name = "in_shopping_lists"