from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.filters import IngredientFilter, RecipeFilter
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
)
from recipes.permissions import IsAuthorOrReadOnly
from recipes.querysets import recipe_queryset
from recipes.serializers import (
    IngredientSerializer,
    RecipeMinifiedSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
)


WRITE_ACTIONS = ('create', 'update', 'partial_update', 'destroy')
PRIVATE_ACTIONS = (
    'favorite',
    'shopping_cart',
    'download_shopping_cart',
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (AllowAny,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')
    filterset_class = RecipeFilter

    def get_queryset(self):
        return recipe_queryset(self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def get_permissions(self):
        if self.action in PRIVATE_ACTIONS or self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _change_relation(self, request, model):
        recipe = self.get_object()
        relation = model.objects.filter(user=request.user, recipe=recipe)
        if request.method == 'DELETE':
            if not relation.exists():
                return Response(
                    {'errors': 'Рецепта нет в списке.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            relation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if relation.exists():
            return Response(
                {'errors': 'Рецепт уже добавлен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        model.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeMinifiedSerializer(
            recipe,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=('post', 'delete'))
    def favorite(self, request, pk=None):
        return self._change_relation(request, Favorite)

    @action(detail=True, methods=('post', 'delete'))
    def shopping_cart(self, request, pk=None):
        return self._change_relation(request, ShoppingCart)

    @action(detail=False, methods=('get',))
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_carts__user=request.user,
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name')
        )
        lines = []
        for item in ingredients:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            lines.append(f'{name} ({unit}) — {item["total"]}')
        lines.sort()
        content = '\n'.join(lines)
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )
        return response

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
        permission_classes=(AllowAny,),
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        link = request.build_absolute_uri(f'/s/{recipe.short_code}')
        return Response({'short-link': link})


def short_link_redirect(request, code):
    recipe = get_object_or_404(Recipe, short_code=code)
    return redirect(f'/recipes/{recipe.pk}')
