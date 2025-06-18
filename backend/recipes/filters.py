import django_filters
from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Dish


class IngredientFilter(FilterSet):
    name = filters.CharFilter(
        field_name="name",
        lookup_expr="istartswith",
        help_text="Поиск ингредиентов по началу названия"
    )

    class Meta:
        model = Ingredient
        fields = ("name",)


class DishFilter(FilterSet):
    author = filters.NumberFilter(
        field_name="author__id",
        help_text="ID автора рецепта"
    )
    is_favorited = filters.BooleanFilter(
        method="filter_favorites",
        help_text="Фильтр по избранным рецептам"
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_shopping_cart",
        help_text="Фильтр по рецептам в списке покупок"
    )

    def filter_favorites(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                favorites__user=self.request.user
            )
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                shopping_carts__user=self.request.user
            )
        return queryset

    class Meta:
        model = Dish
        fields = (
            "author",
            "is_favorited",
            "is_in_shopping_cart",
        )