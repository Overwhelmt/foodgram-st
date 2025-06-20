from djoser.views import UserViewSet
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from api.pagination import CustomPageNumberPagination
from api.serializers import (UserReadSerializer, CustomUserCreateSerializer, 
                             SetAvatarSerializer, UserCreateResponseSerializer)
from users.models import Follow, User
from users.serializers import UserWithRecipesSerializer, SubscribeSerializer


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPageNumberPagination
    permission_classes = (AllowAny,) # Позволяем чтение всем

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        # ИЗМЕНЕНО: Для подписок используется UserWithRecipesSerializer
        if self.action == 'subscriptions':
            return UserWithRecipesSerializer
        return UserReadSerializer

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def get_current_user(self, request):
        serializer = UserReadSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(
        methods=['put', 'delete'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def manage_avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = SetAvatarSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        # ИЗМЕНЕНО: url_path соответствует спецификации
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        followed_users = User.objects.filter(followers__follower=request.user)
        page = self.paginate_queryset(followed_users)
        serializer = self.get_serializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='subscribe'
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            serializer = SubscribeSerializer(
                data={'follower': request.user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        

        subscription = User.objects.filter(creator_subscriptions__follower=request.user)
        if not subscription.exists():
            return Response({'errors': 'Вы не были подписаны на этого пользователя.'}, status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            UserCreateResponseSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        return obj.author == request.user