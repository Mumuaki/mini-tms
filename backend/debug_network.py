import asyncio
import json
import sys
from playwright.async_api import async_playwright

async def run():
    print("Подключение к браузеру...")
    async with async_playwright() as p:
        # Подключаемся к уже открытому браузеру по CDP
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            if not context.pages:
                print("Нет открытых вкладок. Откройте Trans.eu в браузере.")
                return
            page = context.pages[0]
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            print("Убедитесь, что браузер запущен через зеленую кнопку 'Open Browser'.")
            return

        print(f"Успешно подключено к странице: {page.url}")
        print("-" * 50)
        print("ОЖИДАНИЕ СЕТЕВЫХ ЗАПРОСОВ...")
        print("Пожалуйста, нажмите кнопку 'ПОИСК' (Search) на странице Trans.eu прямо сейчас!")
        print("Или измените фильтры, чтобы список обновился.")
        print("-" * 50)

        async def handle_response(response):
            try:
                # Фильтруем только JSON ответы
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    url = response.url
                    
                    # Ищем ключевые слова в URL, которые похожи на API грузов
                    keywords = ["offers", "freights", "loads", "search", "api"]
                    if any(k in url for k in keywords):
                        print(f"\n[+] ПОЙМАН ЗАПРОС: {url}")
                        
                        try:
                            # Пытаемся получить тело ответа
                            data = await response.json()
                            
                            # Проверяем, похоже ли это на список грузов
                            is_list = isinstance(data, list)
                            has_items = isinstance(data, dict) and ("items" in data or "offers" in data)
                            
                            snippet = str(data)[:300]
                            print(f"    Тип данных: {'Список' if is_list else 'Объект'}")
                            print(f"    Сниппет: {snippet}...")
                            
                            # Если нашли что-то стоящее, сохраняем пример в файл
                            if is_list and len(data) > 0:
                                with open("api_sample_list.json", "w", encoding="utf-8") as f:
                                    json.dump(data, f, indent=2, ensure_ascii=False)
                                print("    !!! СОХРАНЕНО в api_sample_list.json !!!")
                                
                            if has_items:
                                with open("api_sample_dict.json", "w", encoding="utf-8") as f:
                                    json.dump(data, f, indent=2, ensure_ascii=False)
                                print("    !!! СОХРАНЕНО в api_sample_dict.json !!!")

                        except Exception as e:
                            print(f"    Ошибка чтения JSON: {e}")

            except Exception as e:
                pass

        # Подписываемся на события
        page.on("response", handle_response)
        
        # Ждем 60 секунд действий пользователя
        for i in range(60):
            if i % 10 == 0:
                print(f"Слушаю... {60-i} сек.")
            await asyncio.sleep(1)

        print("Завершение прослушивания.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run())
