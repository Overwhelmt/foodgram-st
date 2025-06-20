import json
from pathlib import Path
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = 'Загружает список ингредиентов из JSON в базу данных'

    def handle(self, *args, **options):
        json_file_path = Path(__file__).resolve().parent.parent.parent / 'data' / 'ingredients.json'
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                ingredients_data = json.load(file)
            for item in ingredients_data:
                name = item.get('name')
                measurement_unit = item.get('measurement_unit')
                if name and measurement_unit:
                    Ingredient.objects.update_or_create(
                        name=name,
                        defaults={'measurement_unit': measurement_unit}
                    )
                    self.stdout.write(self.style.SUCCESS(f'Успешно добавлен/обновлен ингредиент: {name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Нет данных для ингредиента: {item}'))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Файл {json_file_path} не существует'))
