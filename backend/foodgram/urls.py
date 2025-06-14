from django.contrib import admin
from django.urls import include, path

from recipes.views import DishViewSet

urlpatterns = [
    path("admin/", admin.site.urls),
    
    path("api/", include("api.urls", namespace="api")),
    
    path(
        "s/<int:pk>/",
        DishViewSet.as_view({"get": "retrieve"}),
        name="recipe-short-link"
    ),

]