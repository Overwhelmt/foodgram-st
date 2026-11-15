import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из data/ingredients.csv'

    def handle(self, *args, **options):
        path = self._find_file()
        existing = set(
            Ingredient.objects.values_list('name', 'measurement_unit'),
        )
        created = []
        with path.open(encoding='utf-8-sig', newline='') as csv_file:
            for name, unit in csv.reader(csv_file):
                name = name.strip()
                unit = unit.strip()
                if not name or (name, unit) in existing:
                    continue
                created.append(
                    Ingredient(name=name, measurement_unit=unit),
                )
                existing.add((name, unit))
        Ingredient.objects.bulk_create(created)
        self.stdout.write(
            self.style.SUCCESS(f'Добавлено ингредиентов: {len(created)}'),
        )

    def _find_file(self):
        candidates = (
            Path(settings.BASE_DIR) / 'data' / 'ingredients.csv',
            Path(settings.BASE_DIR).parent / 'data' / 'ingredients.csv',
        )
        for path in candidates:
            if path.exists():
                return path
        raise FileNotFoundError(
            'Не найден data/ingredients.csv рядом с проектом.'
        )
