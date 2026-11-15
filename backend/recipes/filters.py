import django_filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(django_filters.FilterSet):
    author = django_filters.NumberFilter(field_name='author__id')
    is_favorited = django_filters.NumberFilter(method='filter_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(method='filter_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')

    def filter_favorited(self, queryset, name, value):
        return self._filter_flag(queryset, 'favorites', value)

    def filter_cart(self, queryset, name, value):
        return self._filter_flag(queryset, 'shopping_carts', value)

    def _filter_flag(self, queryset, relation, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        lookup = {f'{relation}__user': user}
        if value:
            return queryset.filter(**lookup)
        return queryset.exclude(**lookup)
