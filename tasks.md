# Tasks: TMSmini Gemini-v1

**Status**: In Progress
**Branch**: `gemini-v1`

## Phase 1: Базовая архитектура и Исправления (Frontend)

- [x] **TASK-1.1**: Исправить роутинг в `App.jsx`. Добавить маршрут `/freights`, ведущий на `FreightList`.
- [x] **TASK-1.2**: Унифицировать Layout. Перенести логику навигации из `src/components/Layout.jsx` в `src/components/layout/DashboardLayout.jsx` (или наоборот, выбрав лучший вариант) и удалить дубликат. Убедиться, что ссылки на "My Trucks" и "Freights" работают.
- [x] **TASK-1.3**: Обновить модель БД `Truck` в `backend/app/models.py`. Добавить поля: `max_payload` (Float), `cargo_length`, `cargo_width`, `cargo_height`. (Примечание: габариты уже могут быть, проверить `max_payload`).
- [x] **TASK-1.4**: Обновить модель БД `Freight` в `backend/app/models.py`. Убедиться, что есть все поля для скрапинга.
- [x] **TASK-1.5**: Пересоздать базу данных (`dev.db` или выполнить миграцию), чтобы применить изменения схемы.

## Phase 2: Управление Флотом (Backend + Frontend)

- [x] **TASK-2.1**: Обновить Pydantic схемы в `backend/app/schemas.py` для `Truck` (включить новые поля).
- [x] **TASK-2.2**: Обновить эндпоинты в `backend/app/api/page_routes.py` (или где лежит логика) для сохранения новых полей грузовика.
- [x] **TASK-2.3**: Обновить UI форму "Add/Edit Truck" на фронтенде (`TrucksPage.jsx` или компонент модалки), добавив инпуты для Габаритов и Грузоподъемности.

## Phase 3: Скрапер Логика (Backend Core)

- [x] **TASK-3.1**: Реализовать функцию `launch_browser` в `scraper_manager.py`.
- [x] **TASK-3.2**: Реализовать навигацию к поиску и раскрытие фильтров (шаг "Expand Filters").
- [x] **TASK-3.3**: Реализовать заполнение формы поиска: Origin (GPS/Manual), Destination, Dates (с конвертацией формата).
- [x] **TASK-3.4**: Реализовать парсинг результатов (Data Extraction) + Фильтрация по `max_payload` (если Trans.eu не фильтрует).
- [x] **TASK-3.5**: Сохранение результатов в БД (Upsert logic).

## Phase 4: Визуализация и UX (Frontend Polish)

- [x] **TASK-4.1**: Добавить пагинацию в `FreightList.jsx`.
- [x] **TASK-4.2**: Реализовать сортировку (Client-side) в таблице грузов.
- [x] **TASK-4.3**: Стилизовать таблицу ("Premium" look) - hover effects, badges.
- [x] **TASK-4.4**: Интегрировать кнопку "Start Scraper" с выбором грузовика (Modal).
