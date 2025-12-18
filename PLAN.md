# Implementation Plan: TMSmini Gemini-v1

**Branch**: `gemini-v1`
**Date**: 2025-12-16
**Specs**: [SPECIFICATION.md](./SPECIFICATION.md), [CHECKLIST.md](./CHECKLIST.md)

## Summary

Реализация основного функционала Mini-TMS: автоматизированный скрапинг грузов с Trans.eu, управление автопарком и визуализация данных в "премиальном" UI. 

Технический подход:
- **Backend:** Python/FastAPI для API, Playwright для скрапинга, SQLAlchemy для работы с БД.
- **Frontend:** React/Vite + Tailwind CSS для современного UI.

## Technical Context

**Language/Version**: Python 3.11+, Node.js 20+
**Frameworks**: FastAPI, React 19, Tailwind CSS
**Storage**: SQLite (dev) -> PostgreSQL (prod)
**Scraping**: Playwright (Headless/Headed)
**Testing**: Не предусмотрено на данном этапе (согласно current state), упор на ручное тестирование по чек-листу.

## Project Structure

```text
TMSmini_.vGemini/
├── backend/
│   ├── app/
│   │   ├── models.py           # Обновление моделей (Truck, Freight)
│   │   ├── schemas.py          # Pydantic схемы (API контракты)
│   │   ├── services/
│   │   │   ├── scraper_manager.py # Логика скрапинга (Playwright)
│   │   │   └── trans_eu.py     # Вспомогательные функции
│   │   └── api/routes/         # Эндпоинты (freights, trucks)
│   ├── run_scraper.py          # Скрипт запуска (CLI)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # UI компоненты
│   │   ├── pages/
│   │   │   ├── FreightList.jsx # Таблица грузов (Основной UI)
│   │   │   └── TrucksPage.jsx  # Управление флотом
│   │   ├── services/api.js     # API клиент
│   │   └── App.jsx             # Роутинг (Исправление)
│   └── package.json
└── SPECIFICATION.md
```

## Implementation Phases

### Phase 1: Базовая архитектура и Исправления (Frontend)

**Цель:** Восстановить работоспособность фронтенда и подготовить базу для данных.

1. **Frontend Fixes**:
    - Добавить маршрут `/freights` в `App.jsx`.
    - Унифицировать Layout (удалить дубликаты).
2. **Database Models**:
    - Обновить `models.py`: добавить поля габаритов в `Truck`, уточнить поля в `Freight`.
    - Выполнить миграцию (или пересоздать dev.db).

### Phase 2: Управление Флотом (Backend + Frontend)

**Цель:** Позволить пользователю создавать грузовики с габаритами для точного поиска.

1. **Backend API**:
    - Реализовать CRUD для `Trucks` корректно обрабатывающий новые поля (`cargo_length` и т.д.).
2. **Frontend UI**:
    - Обновить форму добавления грузовика: добавить инпуты для габаритов.

### Phase 3: Скрапер Логика (Backend Core)

**Цель:** Реализовать надежный скрапинг с учетом 17-шагового сценария и фильтров.

1. **Browser Control**:
    - Настроить `launch_browser` и контекст Playwright.
    - Реализовать переход на страницу поиска и нажатие "Expand Filters".
2. **Filter Application**:
    - Реализовать заполнение полей "Откуда" (GPS грузовика или внесенное пользователем) и "Куда".
    - Реализовать выбор дат.
3. **Data Parsing & Filtering**:
    - Парсинг таблицы результатов.
    - **Важно:** Фильтрация по весу/габаритам на лету (если Trans.eu не дает точных фильтров).
    - Сохранение в БД (upsert по `trans_id`).

### Phase 4: Визуализация и UX (Frontend Polish)

**Цель:** Сделать таблицу грузов удобной и красивой ("Premium").

1. **Freight Table**:
    - Внедрить сортировку (клиентскую) по расстоянию/цене.
    - Добавить пагинацию.
    - Стилизация: Hover эффекты, статусы (значки "Deal").
    - Кнопка "Запустить скрапер" с выбором грузовика.

## Risky Areas & Mitigation

1. **Trans.eu DOM Changes**: Скрапер может ломаться при смене верстки.
    - *Mitigation*: Использовать надежные локаторы (text-based, a11y roles) там, где возможно. Логирование ошибок.
2. **Anti-Bot Protection**:
    - *Mitigation*: Использовать существующий профиль браузера (persistent context) и ручной/полуавтоматический режим запуска (headed mode).

## Next Steps

1. Выполнить команду `/speckit.tasks` для генерации атомарных задач.
2. Приступить к Phase 1 (Frontend Fixes).
