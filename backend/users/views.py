from django.db.models import Count
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import Subscription, User
from users.serializers import AvatarSerializer, SubscriptionSerializer


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()

    def get_permissions(self):
        private = (
            'me',
            'set_password',
            'avatar',
            'subscribe',
            'subscriptions',
        )
        if self.action in private:
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=('put', 'delete'),
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=('get',))
    def subscriptions(self, request):
        queryset = User.objects.filter(
            subscribers__user=request.user,
        ).annotate(
            recipes_count=Count('recipes'),
        ).order_by('-subscribers__id')
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=('post', 'delete'))
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        subscription = Subscription.objects.filter(
            user=request.user,
            author=author,
        )
        if request.method == 'DELETE':
            if not subscription.exists():
                return Response(
                    {'errors': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if request.user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if subscription.exists():
            return Response(
                {'errors': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        Subscription.objects.create(user=request.user, author=author)
        author.recipes_count = author.recipes.count()
        serializer = SubscriptionSerializer(
            author,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
