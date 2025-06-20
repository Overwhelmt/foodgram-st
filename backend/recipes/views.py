# recipes/views.py

from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.urls import reverse

from api.pagination import CustomPageNumberPagination
from api.permissions import IsOwnerOrReadOnly
from recipes.filters import IngredientFilter, RecipeFilter
from recipes.models import (FavoriteRecipe, Ingredient, RecipeIngredient, Recipe,
                            ShoppingList)
# ИЗМЕНЕНО: импорты сериализаторов обновлены
from recipes.serializers import (RecipeCreateSerializer, FavoriteSerializer,
                                 RecipeListSerializer, ShoppingListSerializer,
                                 BasicIngredientSerializer, RecipeMinifiedSerializer)

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = BasicIngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    # Убираем search_fields, т.к. фильтрация уже определена в IngredientFilter
    # search_fields = ("^name",)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-publication_date')
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        # ИЗМЕНЕНО: сериализаторы для разных действий
        if self.action in ("list", "retrieve"):
            return RecipeListSerializer
        return RecipeCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def _add_or_remove_relation(self, request, pk, serializer_class, model_class, error_message):
        recipe = get_object_or_404(Recipe, pk=pk)
        
        if request.method == "POST":
            if model_class.objects.filter(user=request.user, recipe=recipe).exists():
                return Response({'errors': error_message['already_exists']}, status=status.HTTP_400_BAD_REQUEST)
            serializer = serializer_class(data={'user': request.user.id, 'recipe': recipe.id}, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            # ИЗМЕНЕНО: Ответ соответствует схеме RecipeMinified
            response_serializer = RecipeMinifiedSerializer(recipe)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            if not model_class.objects.filter(user=request.user, recipe=recipe).exists():
                return Response({'errors': error_message['not_exists']}, status=status.HTTP_400_BAD_REQUEST)
            model_class.objects.filter(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        # ИЗМЕНЕНО: url_path соответствует спецификации
        url_path="favorite",
    )
    def favorite(self, request, pk=None):
        return self._add_or_remove_relation(
            request, pk, FavoriteSerializer, FavoriteRecipe,
            {'already_exists': 'Рецепт уже в избранном', 'not_exists': 'Рецепта нет в избранном'}
        )

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        # ИЗМЕНЕНО: url_path соответствует спецификации
        url_path="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        return self._add_or_remove_relation(
            request, pk, ShoppingListSerializer, ShoppingList,
            {'already_exists': 'Рецепт уже в списке покупок', 'not_exists': 'Рецепта нет в списке покупок'}
        )

    @action(
        detail=False,
        methods=["get",],
        permission_classes=[IsAuthenticated],
        # ИЗМЕНЕНО: url_path соответствует спецификации
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                # ИЗМЕНЕНО: shopping_cart_items - новый related_name
                recipe__shopping_cart_items__user=request.user
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total=Sum("amount"))
            .order_by("ingredient__name")
        )
        
        shopping_list = "Список покупок:\n\n"
        shopping_list += "\n".join(
            f"- {item['ingredient__name']} ({item['ingredient__measurement_unit']}) — {item['total']}"
            for item in ingredients
        )
        
        response = HttpResponse(shopping_list, content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(
        detail=True,
        methods=["get",],
        permission_classes=[AllowAny],
        # ИЗМЕНЕНО: url_path и логика соответствуют спецификации
        url_path="get-link",
    )
    def get_short_link(self, request, pk=None):
        # ИЗМЕНЕНО: генерация короткой ссылки через reverse
        short_link = request.build_absolute_uri(reverse('recipe-short-link', kwargs={'pk': pk}))
        return Response({
            "short-link": short_link
        })