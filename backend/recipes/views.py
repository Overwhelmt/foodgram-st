from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                      IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.pagination import CustomPagination
from api.permissions import IsOwnerOrReadOnly
from recipes.filters import IngredientFilter, DishFilter
from recipes.models import (FavoriteRecipe, Ingredient, RecipeIngredient, Dish,
                          ShoppingList)
from recipes.serializers import (DishCreateUpdateSerializer, FavoriteSerializer,
                               DishDetailSerializer, ShoppingListSerializer,
                               BasicIngredientSerializer)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = BasicIngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ("^title",)


class DishViewSet(viewsets.ModelViewSet):
    queryset = Dish.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = DishFilter

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return DishDetailSerializer
        return DishCreateUpdateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="mark-favorite",
    )
    def favorite_action(self, request, pk=None):
        if request.method == "POST":
            return self._create_relation(
                request, pk, FavoriteSerializer
            )
        return self._remove_relation(
            request,
            pk,
            "favorited_by",
            FavoriteRecipe.DoesNotExist,
            "Рецепт не в избранном"
        )

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="add-to-cart",
    )
    def shopping_cart_action(self, request, pk=None):
        if request.method == "POST":
            return self._create_relation(
                request, pk, ShoppingListSerializer
            )
        return self._remove_relation(
            request,
            pk,
            "in_shopping_lists",
            ShoppingList.DoesNotExist,
            "Рецепт не в списке покупок"
        )

    def _create_relation(self, request, pk, serializer_class):
        serializer = serializer_class(
            data={
                "user": request.user.id,
                "dish": pk,
            },
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_relation(self, request, pk, relation_name, 
                        exception_class, error_message):
        try:
            getattr(request.user, relation_name).filter(dish_id=pk).delete()
        except exception_class:
            return Response(
                {"error": error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=("get",),
        permission_classes=(IsAuthenticated,),
        url_path="export-shopping-list",
    )
    def export_shopping_list(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                dish__in_shopping_lists__user=request.user
            )
            .values("ingredient__title", "ingredient__unit")
            .annotate(total=Sum("quantity"))
            .order_by("ingredient__title")
        )
        
        shopping_list = "\n".join(
            f"{item['ingredient__title']} - {item['total']} {item['ingredient__unit']}"
            for item in ingredients
        )
        
        response = HttpResponse(shopping_list, content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(
        detail=True,
        methods=("get",),
        permission_classes=(IsAuthenticatedOrReadOnly,),
        url_path="share-link",
    )
    def share_dish_link(self, request, pk=None):
        dish = self.get_object()
        return Response({
            "share_url": f"{request.build_absolute_uri('/')}dishes/{dish.id}"
        })