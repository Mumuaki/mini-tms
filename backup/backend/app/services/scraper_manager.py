import asyncio
import os
import subprocess
import sys
from typing import Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)

class ScraperManager:
    """
    Менеджер для управления браузером через CDP.
    
    Гарантии безопасности:
    1. Браузер запускается через отдельный скрипт _playwright_launcher.py, отвязанный от основного процесса.
    2. Метод close() никогда не посылает команду на закрытие браузера, 
       только разрывает соединение.
    3. Использует постоянную папку профиля (user-data-dir), чтобы сессия сохранялась.
    """
    _instance: Optional["ScraperManager"] = None
    
    # Настройки подключения
    CDP_HOST = "127.0.0.1"
    CDP_PORT = 9222
    CDP_URL = f"http://{CDP_HOST}:{CDP_PORT}"
    
    # Путь к профилю (сохраняется рядом со скриптом или в корне проекта)
    # Важно: профиль должен быть постоянным, чтобы не слетала авторизация
    PROFILE_DIR = os.path.abspath(os.path.join(os.getcwd(), "chrome_profile"))

    def __new__(cls) -> "ScraperManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.playwright = None
            cls._instance.browser = None
            cls._instance.context = None
            cls._instance.page = None
            cls._instance.chrome_process = None
        return cls._instance

    # -----------------------------------------------------------------
    # Вспомогательные методы (Асинхронные)
    # -----------------------------------------------------------------
    async def _is_cdp_port_active(self) -> bool:
        """Быстрая проверка, слушает ли кто-то порт 9222."""
        try:
            _, writer = await asyncio.open_connection(self.CDP_HOST, self.CDP_PORT)
            writer.close()
            await writer.wait_closed()
            return True
        except (ConnectionRefusedError, OSError):
            return False

    async def _start_chrome_process(self) -> None:
        """
        Запуск отдельного процесса Chrome через _playwright_launcher.py.
        Этот скрипт запускает браузер и обеспечивает правильную политику asyncio.
        """
        if await self._is_cdp_port_active():
            print("[ScraperManager] Браузер уже запущен, подключаемся...")
            return

        launcher_path = os.path.join(os.path.dirname(__file__), "_playwright_launcher.py")
        
        # Ensure the Python executable for the current venv is used
        python_exe = sys.executable

        args = [
            python_exe,
            launcher_path,
            str(self.CDP_PORT),
            self.PROFILE_DIR,
        ]
        
        print(f"[ScraperManager] Запуск лаунчера: {' '.join(args)}")
        
        # We run the launcher without capturing stdout/stderr, 
        # as the launcher itself prints relevant info and will exit
        self.chrome_process = subprocess.Popen(
            args,
            stdout=sys.stdout, # Changed to sys.stdout to see launcher output
            stderr=sys.stderr, # Changed to sys.stderr to see launcher output
            shell=False,
        )
        
        # Wait for the CDP port to become available, handled by launcher
        # We just wait for the port to be active here.
        for _ in range(30): # Increased timeout for initial launch
            if await self._is_cdp_port_active():
                print("[ScraperManager] ✓ Порт 9222 доступен.")
                return
            await asyncio.sleep(0.5)
        
        if self.chrome_process.poll() is not None:
             print("[ScraperManager] Лаунчер завершился до подключения.")
             raise RuntimeError(f"Лаунчер браузера завершился с кодом {self.chrome_process.poll()}.")

        raise TimeoutError("Браузер запущен, но порт 9222 не отвечает в течение 15 секунд.")

    # -----------------------------------------------------------------
    # Основная логика
    # -----------------------------------------------------------------
    async def launch_browser(self) -> None:
        """Инициализация Playwright и подключение к браузеру."""
        if self.playwright is None:
            self.playwright = await async_playwright().start()

        # 1. Пытаемся подключиться к существующему. Если нет - запускаем.
        if not await self._try_connect():
            await self._start_chrome_process() # This now calls the external launcher
            if not await self._try_connect():  # Fixed: removed redundant await
                raise ConnectionError("Не удалось подключиться к браузеру после запуска.")

        # 2. Получаем страницу
        await self._ensure_page()

    async def _try_connect(self) -> bool:
        """Попытка подключиться по CDP. Возвращает True, если успешно."""
        if self.browser and self.browser.is_connected():
            return True
        try:
            self.browser = await self.playwright.chromium.connect_over_cdp(self.CDP_URL)
            if self.browser.contexts:
                self.context = self.browser.contexts[0]
            else:
                self.context = await self.browser.new_context()
            return True
        except Exception:
            return False

    async def _ensure_page(self):
        """Гарантируем, что есть открытая вкладка."""
        if not self.context.pages:
            self.page = await self.context.new_page()
        else:
            self.page = self.context.pages[0]
        
        try:
            url = self.page.url
        except Exception:
            self.page = await self.context.new_page()
            url = self.page.url
        
        if not url or "about:blank" in url or "chrome://new-tab-page" in url:
            print("[ScraperManager] Пустая вкладка. Переходим на Trans.eu...")
            try:
                await self.page.goto(
                    "https://auth.platform.trans.eu/accounts/login", timeout=10000
                )
            except Exception as e:
                print(f"[ScraperManager] Ошибка навигации (возможно, браузер свернут): {e}")

    async def get_page(self) -> Optional[Page]:
        """Возвращает страницу, восстанавливая соединение при разрыве."""
        if (
            self.page
            and not self.page.is_closed()
            and self.browser
            and self.browser.is_connected()
        ):
            return self.page
        try:
            await self.launch_browser()
            return self.page
        except Exception as e:
            print(f"[ScraperManager] Ошибка получения страницы: {e}")
            return None

    async def close(self) -> None:
        """
        Безопасное отключение от браузера.
        Окно Chrome остается открытым.
        """
        print("[ScraperManager] Отключаем Playwright (Browser остается работать)...")
        if self.playwright:
            await self.playwright.stop()
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

scraper_manager = ScraperManager()
