import base64

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Recipe, RecipeIngredient
from users.models import User

PNG = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8'
    'z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
)

USERS = (
    {
        'email': 'admin@foodgram.ru',
        'username': 'admin',
        'first_name': 'Админ',
        'last_name': 'Фудграм',
        'password': 'adminpass123',
        'is_staff': True,
        'is_superuser': True,
        'recipe': 'Борщ от администратора',
    },
    {
        'email': 'user@foodgram.ru',
        'username': 'fooduser',
        'first_name': 'Иван',
        'last_name': 'Поваров',
        'password': 'userpass123',
        'is_staff': False,
        'is_superuser': False,
        'recipe': 'Каша обычного пользователя',
    },
)


class Command(BaseCommand):
    help = 'Создаёт администратора и пользователя с рецептами'

    def handle(self, *args, **options):
        ingredients = list(Ingredient.objects.all()[:2])
        if len(ingredients) < 2:
            self.stdout.write(
                self.style.ERROR(
                    'Сначала выполните load_ingredients: нужно минимум '
                    'два ингредиента.'
                ),
            )
            return
        for raw in USERS:
            item = raw.copy()
            recipe_name = item.pop('recipe')
            password = item.pop('password')
            is_superuser = item.pop('is_superuser')
            email = item.pop('email')
            user, created = User.objects.get_or_create(
                email=email,
                defaults=item,
            )
            if created:
                user.set_password(password)
                user.is_superuser = is_superuser
                user.save()
            if not user.recipes.exists():
                recipe = Recipe(
                    author=user,
                    name=recipe_name,
                    text='Тестовый рецепт для проверки проекта.',
                    cooking_time=20,
                )
                recipe.image.save(
                    'demo.png',
                    ContentFile(PNG),
                    save=True,
                )
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredients[0],
                    amount=100,
                )
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredients[1],
                    amount=50,
                )
        self.stdout.write(self.style.SUCCESS('Тестовые данные готовы.'))
