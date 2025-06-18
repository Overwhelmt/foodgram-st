from django.contrib import admin
from django.contrib.admin import ModelAdmin, register, TabularInline

from foodgram.constants import INGREDIENT_RECIPE_MIN_AMOUNT
from recipes.models import (FavoriteRecipe, Ingredient, RecipeIngredient, Dish,
                          ShoppingList)
from users.models import Follow


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ("id", "title", "unit")
    search_fields = ("name__istartswith",)
    list_display_links = ("title",)
    ordering = ("title",)


class RecipeIngredientInline(TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = INGREDIENT_RECIPE_MIN_AMOUNT
    fields = ("ingredient", "quantity")
    autocomplete_fields = ("ingredient",)


@register(Dish)
class RecipeAdmin(ModelAdmin):
    list_display = ("id", "title", "author", "favorites_count", "publication_date")
    list_filter = ("author__username",)
    search_fields = ("name__icontains", "author__username")
    inlines = (RecipeIngredientInline,)
    readonly_fields = ("favorites_count",)
    date_hierarchy = "publication_date"

    @admin.display(description="В избранном")
    def favorites_count(self, obj):
        return obj.favorites.count()


@register(RecipeIngredient)
class RecipeCompositionAdmin(ModelAdmin):
    list_display = ("id", "get_recipe", "get_ingredient", "quantity")
    list_select_related = ("dish", "ingredient")
    search_fields = ("dish__name", "ingredient__name")

    @admin.display(description="Рецепт")
    def get_recipe(self, obj):
        return obj.dish.name

    @admin.display(description="Ингредиент")
    def get_ingredient(self, obj):
        return f"{obj.ingredient.name} ({obj.ingredient.measurement_unit})"


@register(ShoppingList)
class UserShoppingCartAdmin(ModelAdmin):
    list_display = ("id", "user", "get_recipe")
    list_select_related = ("user", "dish")
    search_fields = ("user__username", "dish__name")

    @admin.display(description="Рецепт")
    def get_recipe(self, obj):
        return obj.dish.name


@register(Follow)
class FollowAdmin(ModelAdmin):
    list_display = ("id", "follower", "author")
    search_fields = (
        "subscriber__username__istartswith",
        "author__username__istartswith"
    )
    list_filter = ("follower", "author")


@register(FavoriteRecipe)
class FavoriteRecipeRecipeAdmin(ModelAdmin):
    list_display = ("id", "user", "get_recipe")
    list_select_related = ("user", "dish")
    search_fields = ("user__username", "dish__name")

    @admin.display(description="Рецепт")
    def get_recipe(self, obj):
        return obj.dish.name