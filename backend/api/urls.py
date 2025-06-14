from django.urls import include, path
from rest_framework import routers

from api.views import CustomUserViewSet
from recipes.views import IngredientViewSet, DishViewSet

router = routers.DefaultRouter()
router.register(
    "ingredients", 
    IngredientViewSet, 
    basename="ingredients"
)
router.register(
    "dishes",
    DishViewSet,
    basename="recipes"
)
router.register(
    "users", 
    CustomUserViewSet, 
    basename="users"
)

urlpatterns = [
    path("", include(router.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    path(
        "users/me/avatar/", 
        CustomUserViewSet.as_view({
            'put': 'manage_avatar', 
            'delete': 'manage_avatar'
        }), 
        name="user-avatar"
    ),
    path(
        "users/<int:pk>/follow/",
        CustomUserViewSet.as_view({
            'post': 'manage_follow',
            'delete': 'manage_follow'
        }),
        name="user-follow"
    ),
]

app_name = "api"