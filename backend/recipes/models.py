import uuid

from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Ingredient(models.Model):
    name = models.CharField('название', max_length=128)
    measurement_unit = models.CharField('единица измерения', max_length=64)

    class Meta:
        ordering = ('id',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient',
            ),
        )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='автор',
    )
    name = models.CharField('название', max_length=256)
    image = models.ImageField('картинка', upload_to='recipes/images/')
    text = models.TextField('описание')
    cooking_time = models.PositiveSmallIntegerField(
        'время приготовления',
        validators=(MinValueValidator(1),),
    )
    short_code = models.CharField(
        'короткий код',
        max_length=8,
        unique=True,
        blank=True,
    )
    created_at = models.DateTimeField('дата публикации', auto_now_add=True)

    class Meta:
        ordering = ('-created_at', '-id')
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self._build_short_code()
        super().save(*args, **kwargs)

    @classmethod
    def _build_short_code(cls):
        for _ in range(10):
            code = uuid.uuid4().hex[:6]
            if not cls.objects.filter(short_code=code).exists():
                return code
        return uuid.uuid4().hex


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name='recipe_ingredients',
        verbose_name='ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'количество',
        validators=(MinValueValidator(1),),
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'ингредиент в рецепте'
        verbose_name_plural = 'ингредиенты в рецепте'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            ),
        )

    def __str__(self):
        return f'{self.ingredient} — {self.amount}'


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='рецепт',
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(app_label)s_%(class)s_unique',
            ),
        )


class Favorite(UserRecipeRelation):
    class Meta:
        default_related_name = 'favorites'
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite',
            ),
        )

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное'


class ShoppingCart(UserRecipeRelation):
    class Meta:
        default_related_name = 'shopping_carts'
        verbose_name = 'список покупок'
        verbose_name_plural = 'списки покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart',
            ),
        )

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в покупки'
