from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from api.pagination import CustomPageNumberPagination
from api.serializers import (UserReadSerializer, UserCreateSerializer, 
                            UserAvatarUpdateSerializer)
from users.models import Follow, User
from users.serializers import (FollowCreateSerializer, FollowCreateSerializer)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserReadSerializer

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def get_current_user(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        methods=['put', 'delete'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def manage_avatar(self, request):
        if request.method == 'PUT':
            return self._update_avatar(request)
        return self._delete_avatar(request)

    def _update_avatar(self, request):
        serializer = UserAvatarUpdateSerializer(
            request.user, 
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='followings'
    )
    def list_followings(self, request):
        followings = User.objects.filter(
            creator_subscriptions__follower=request.user
        )
        page = self.paginate_queryset(followings)
        serializer = FollowCreateSerializer(
            page, 
            many=True, 
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='follow'
    )
    def manage_follow(self, request, pk=None):
        if request.method == 'POST':
            return self._create_follow(request, pk)
        return self._delete_follow(request, pk)

    def _create_follow(self, request, user_id):
        serializer = FollowCreateSerializer(
            data={
                'follower': request.user.id,
                'author': user_id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _delete_follow(self, request, user_id):
        try:
            author = User.objects.get(pk=user_id)
            subscription = Follow.objects.get(
                follower=request.user,
                author=author
            )
            subscription.delete()
            return Response(
                {'detail': f'Вы отписались от {author.login}'},
                status=status.HTTP_204_NO_CONTENT
            )
        except User.DoesNotExist:
            raise NotFound('Пользователь не найден')
        except Follow.DoesNotExist:
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )