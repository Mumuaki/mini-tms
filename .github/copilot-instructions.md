## Quick context

This repo is a small Transport Management System (TMS) with a React frontend and a FastAPI backend. The backend contains several automation/scraping services (Playwright, Trans.eu scraper, GPS and Google Maps helpers) that are intentionally run as separate processes or background tasks.

## Architecture (big picture)

- **Frontend**: [frontend](frontend) — React + Vite SPA. Run with `npm run dev`.
- **Backend**: [backend](backend) — FastAPI app under `backend/app` with:
  - `app.main` — HTTP endpoints and FastAPI wiring.
  - `app.services/*` — service layer (Playwright, scrapers, GPS, Google Maps, tasks).
  - `app.models` / `app.schemas` — SQLAlchemy + Pydantic (pydantic v2 usage: `model_dump`).
  - `database.py` — DB session provider and engine.
- **Browser automation**: Playwright is launched in a separate process by `_playwright_launcher.py` and managed by `scraper_manager` (connects over CDP at port 9222). The persistent Chrome profile lives in the `chrome_profile` folder to preserve manual login.

## Important developer workflows & commands

- Backend venv + deps (from repo root):

  ```powershell
  cd backend
  python -m venv .venv
  .venv\Scripts\activate
  pip install -r requirements.txt
  ```

- Database migrations (Alembic):

  ```powershell
  cd backend
  alembic -c alembic.ini upgrade head
  ```

- Run backend (Windows note):
  - Use `python backend/run.py` on Windows to ensure the correct asyncio event loop policy for Playwright (this script sets WindowsProactorEventLoopPolicy and runs uvicorn without `--reload`).
  - If you use `uvicorn app.main:app`, prefer `reload=False` on Windows to avoid Playwright subprocess issues.

- Start frontend:

  ```bash
  cd frontend
  npm install
  npm run dev
  ```

- Launch browser for manual Trans.eu login
  - Either call the backend endpoint `POST /scraper/launch` or run the launch script indirectly via `ScraperManager` which starts `_playwright_launcher.py` and exposes CDP on port 9222.
  - Profile folder: `chrome_profile` — keep it persistent to retain manual login.

## Project-specific patterns & conventions

- Services vs endpoints: business logic lives in `app.services/*`. Endpoints in `app.main` are thin and call into services (e.g., `run_scraper_task`, `scraper_manager`). Prefer adding new automation logic to `services` and keep routes minimal.
- Playwright pattern: don't embed Playwright startup in the main process. Use `_playwright_launcher.py` + `ScraperManager` which connects over CDP (`connect_over_cdp`) to a running browser.
- Background tasks: use FastAPI `BackgroundTasks` (see `/freights/scrape`) and `services.tasks.run_scraper_task` for long-running scraping.
- Pydantic v2 idioms: code uses `model_dump(exclude_unset=True)` to get partial updates; follow this pattern when constructing or updating models.
- DB sessions: endpoints use `Depends(database.get_db)` — follow the same dependency injection pattern to get sessions and commit/refresh objects.

## Tests and CI notes

- Tests live in `Tests/` and `backend` has `pytest.ini`. Run from repo root with a backend venv active:

  ```powershell
  cd backend
  pytest -q
  ```

- Some tests mock external services; be cautious running integration-style tests that expect Playwright or external credentials.

## Integration points & external secrets

- Trans.eu scraping: see `app.services.trans_eu` — requires an authenticated browser session.
- GPS integration: `app.services.gps_service` — check tests for how credentials are provided. Google Maps helpers are in `app.services.google_maps` and rely on API keys from env.
- Environment: copy `.env.example` to `.env` in `backend` and set `DATABASE_URL`, `GOOGLE_MAPS_KEY`, and any GPS credentials before running.

## Quick examples for common edits

- Add a new API route that triggers a scraper task:
  - Add thin endpoint in `app.main` that accepts a `schemas.ScrapeRequest` and delegates to `background_tasks.add_task(run_scraper_task, ...)`.

- Add a new service using Playwright:
  - Add under `app.services`, expose async helpers, and use `scraper_manager.get_page()` to obtain a `Page` object.

## Things to watch out for / gotchas

- Windows-specific asyncio: code explicitly sets `WindowsProactorEventLoopPolicy` — when editing startup code avoid moving that logic after Playwright imports.
- Avoid using `uvicorn --reload` on Windows during development when working with Playwright; prefer `python backend/run.py`.
- Persistent browser profile is required for manual login flow. Deleting `chrome_profile` will force re-login.

---

If anything here is unclear or you want additional examples (sample tests, a contributor checklist, or CI steps), tell me which area to expand and I will iterate.
