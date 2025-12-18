import asyncio
import json
import sys
from playwright.async_api import async_playwright

async def run():
    print("Подключение к браузеру для WS отладки...")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            if not browser.contexts:
                print("Нет контекстов.")
                return
            page = browser.contexts[0].pages[0]
        except Exception as e:
            print(f"Ошибка: {e}")
            return

        print(f"Слушаем WS на {page.url}")
        print("Нажмите ПОИСК в браузере...")

        def on_web_socket(ws):
            print(f"[WS] OPEN: {ws.url}")
            ws.on("framesent", lambda payload: print(f"  -> SENT: {str(payload)[:100]}"))
            
            def handle_frame_received(payload):
                text = str(payload)
                # Ищем признаки списка грузов
                if "items" in text and "price" in text:
                    print(f"\n[WS] ПОЙМАНЫ ДАННЫЕ (items+price): {text[:300]}...\n")
                    try:
                        # Попытка распарсить если это JSON-подобное (иногда WS шлет чистый JSON, иногда socket.io формат)
                        # Socket.io обычно '42["event", data]'
                        if text.startswith('42'):
                            json_str = text[2:]
                            data = json.loads(json_str)
                            print("    Распарсенный JSON (Socket.IO):", str(data)[:200])
                            
                            # Сохраняем семпл
                            with open("ws_sample.json", "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                            print("    !!! WS SAMPLE SAVED to ws_sample.json !!!")
                    except:
                        pass
                elif "freight" in text or "offer" in text:
                     print(f"  <- RECV (keyword match): {text[:100]}")

            ws.on("framereceived", handle_frame_received)

        page.on("websocket", on_web_socket)
        
        # Ждем 60 секунд
        for i in range(60):
            await asyncio.sleep(1)
            if i % 10 == 0:
                print(f"{60-i}...")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run())
