from django.db.models import BooleanField, Exists, OuterRef, Value

from recipes.models import Favorite, Recipe, ShoppingCart


def with_user_flags(queryset, user):
    if user.is_authenticated:
        return queryset.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(user=user, recipe=OuterRef('pk')),
            ),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    user=user,
                    recipe=OuterRef('pk'),
                ),
            ),
        )
    return queryset.annotate(
        is_favorited=Value(False, output_field=BooleanField()),
        is_in_shopping_cart=Value(False, output_field=BooleanField()),
    )


def recipe_queryset(user):
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'recipe_ingredients__ingredient',
    )
    return with_user_flags(queryset, user)
