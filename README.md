# Система аутентификации и авторизации на FastAPI

Кратко: FastAPI + PostgreSQL, своя аутентификация (JWT-сессии) и авторизация RBAC с детальными правами на ресурсы. Тестовые данные создаются через seed.

## Возможности
- Регистрация, логин/логаут, мягкое удаление (is_active=False)
- JWT Bearer, сессии в БД
- Роли: admin, manager, user, guest
- Ресурсы: users, products, orders, stores, permissions
- Права: read/read_all/create/update/update_all/delete/delete_all
- Админ-API для ролей, ресурсов и правил
- Mock-ресурсы: products, orders, stores

## Быстрый старт (Docker)
```bash
cd "/Users/nurbolat.satybaldy/Desktop/ТЗ"
docker-compose -p tz up -d --build
# БД на хост-порту 5433, API на 8000
```
Swagger: http://localhost:8000/docs  
Health: http://localhost:8000/health

## Локальный запуск без Docker
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

createdb auth_system  # создайте БД в Postgres
cp .env.example .env  # при необходимости поправьте DATABASE_URL и SECRET_KEY

python seed_data.py
uvicorn main:app --reload
```

## Тестовые учётки (после seed_data.py)
- admin@example.com / admin123
- manager@example.com / manager123
- user@example.com / user123
- guest@example.com / guest123

## Основные эндпоинты
- Аутентификация: `/auth/register`, `/auth/login`, `/auth/logout`, `/auth/me`
- Пользователь: `/users/me` (GET/PUT/DELETE)
- Админ: `/admin/roles`, `/admin/elements`, `/admin/access-rules`, `/admin/users`
- Ресурсы (mock): `/resources/products`, `/resources/orders`, `/resources/stores`

## Структура
```
ТЗ/
├── main.py
├── config.py
├── database.py
├── models.py
├── schemas.py
├── security.py
├── dependencies.py
├── seed_data.py
├── requirements.txt
├── docker-compose.yml
└── routers/
    ├── auth.py
    ├── users.py
    ├── admin.py
    └── mock_resources.py
```

## Права (кратко)
- Admin: полный доступ
- Manager: полный доступ к products/orders/stores, чтение users
- User: читать products/stores, CRUD только по своим orders
- Guest: читать products/stores

Примечания:
- В docker-compose БД слушает 5433 на хосте (чтобы не конфликтовать с локальным 5432).
- Хеширование через bcrypt_sha256, даты в UTC.

