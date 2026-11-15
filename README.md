# Фудграм

Сервис публикации рецептов. Фронтенд уже собран в `frontend`. Бэкенд — Django REST API в `backend`, контракт описан в `docs/openapi-schema.yml`.

## Локальный запуск API

Команды ниже рассчитаны на проверку Postman-коллекцией: база SQLite, сервер на порту 8000.

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py load_ingredients
python manage.py runserver 127.0.0.1:8000
```

В Postman импортируйте `postman_collection/foodgram.postman_collection.json` и запустите коллекцию. Адрес по умолчанию: `http://127.0.0.1:8000`.

Повторный прогон после очистки тестовых пользователей:

```bash
bash postman_collection/clear_db.sh
```

## Тестовые пользователи

Команда `python manage.py load_demo` создаёт две учётные записи и по одному рецепту. Перед ней нужны ингредиенты.

| Роль | Email | Пароль |
| --- | --- | --- |
| Администратор | admin@foodgram.ru | adminpass123 |
| Пользователь | user@foodgram.ru | userpass123 |

Админка: `http://127.0.0.1:8000/admin/`.

## Docker

Из каталога `infra`:

```bash
cp .env.example .env
docker compose up --build
```

Сайт: `http://localhost`. Документация API: `http://localhost/api/docs/`.

Сервисы: nginx, PostgreSQL, backend (Gunicorn), frontend только для сборки статики. Данные базы, медиа и статика лежат в volumes. При старте выполняются миграции, загрузка ингредиентов и тестовых пользователей.

## CI

При пуше в `main` GitHub Actions запускает flake8 и публикует образ `DOCKER_USERNAME/foodgram-backend`. Логин Docker Hub хранится в секретах репозитория, не в коде.

## Что умеет API

Регистрация и вход по email с токеном, аватар, смена пароля, рецепты с картинкой в base64, избранное, список покупок одним текстовым файлом с суммированием ингредиентов, подписки и короткая ссылка `/s/<код>`.
