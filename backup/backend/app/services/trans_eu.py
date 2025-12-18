import asyncio
from typing import List, Dict, Optional
from playwright.async_api import Page
import traceback
import re
import hashlib

class TransEuScraper:
    """
    Сервис для работы со страницей поиска грузов Trans.eu.
    Оптимизирован под реальный UI Trans.eu (React, Shadow DOM, Modal behavior).
    """

    def __init__(self, page: Page):
        self.page = page
        self.freights_url = "https://platform.trans.eu/exchange/offers"

    async def ensure_on_search_page(self):
        """Проверка, что мы на странице поиска грузов."""
        if "exchange/offers" not in self.page.url:
            print(f"Navigating to {self.freights_url}...")
            await self.page.goto(self.freights_url, wait_until="domcontentloaded", timeout=60_000)
            await asyncio.sleep(2)
        else:
            print("Already on offers page.")

    async def search_freights(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Основной флоу: Проверка -> Фильтры -> Парсинг.
        """
        await self.ensure_on_search_page()

        # Ждем основной контент
        try:
            print("Waiting for freight list container...")
            await self.page.wait_for_selector('main', timeout=15_000)
        except Exception as e:
            print(f"Warning: Main content wait timeout: {e}")

        if filters:
            await self._apply_filters(filters)

        return await self._parse_freight_list()

    async def _apply_filters(self, filters: Dict):
        """
        Применение фильтров ПО ИНСТРУКЦИИ ПОЛЬЗОВАТЕЛЯ.
        """
        print(f"Applying filters: {filters}")
        
        # Scroll to top to ensure elements are visible
        try: await self.page.evaluate("window.scrollTo(0, 0)")
        except: pass

        # 1. Локации (Шаги 1-7 из инструкции)
        if "origin" in filters:
            await self._set_location("Загрузка", filters["origin"])
        
        if "destination" in filters:
            await self._set_location("Разгрузка", filters["destination"])

        # 2. Expand Filters
        await self._ensure_filters_expanded()

        # 3. Даты - USING JS HACK for Readonly fields
        await self._set_dates(
            "Loading date", 
            filters.get("loading_date_from"), 
            filters.get("loading_date_to")
        )
        await self._set_dates(
            "Unloading date", 
            filters.get("unloading_date_from"), 
            filters.get("unloading_date_to")
        )

        # 5. Поиск (Шаг 17)
        await self._click_search_button()

    async def _ensure_filters_expanded(self):
        """Разворачивает панель фильтров."""
        try:
            for label in ["Expand filters", "More filters", "Rozwiń filtry", "Развернуть фильтры", "Filters"]:
                expand_btn = self.page.get_by_role("button", name=re.compile(label, re.I)).first
                if await expand_btn.count() > 0 and await expand_btn.is_visible():
                    print(f"Clicking '{label}' to show dates/weight...")
                    await expand_btn.click()
                    await asyncio.sleep(0.5)
                    return
        except Exception:
            pass



    async def _set_location(self, label: str, value: str): # Loading / Unloading
        """
        Реализация алгоритма пользователя (Пункты 1-9).
        """
        if not value: return

        print(f"Setting location '{label}' to '{value}'")
        try:
            # 1. Находим поле 'Загрузка'/'Разгрузка' (Шаг 1)
            # data-ctx самый надежный
            ctx_selector = ""
            if label == "Загрузка": ctx_selector = '[data-ctx="place-loading_place-0"]'
            elif label == "Разгрузка": ctx_selector = '[data-ctx="place-unloading_place-0"]'
            
            container = self.page.locator(ctx_selector).first
            if await container.count() == 0:
                 print(f"(!) Input container for {label} not found")
                 return
            
            # Clear existing value if possible
            try:
                # Look for typical clear buttons (often svg icons inside generic buttons)
                clear_btns = container.locator("button").all()
                for btn in await clear_btns:
                     if await btn.is_visible():
                         # Check if it looks like a clear button (e.g. no text, small size) or explicitly labelled
                         # Just clicking visible buttons in the input container is usually safe (dropdown arrow or clear)
                         # If it's a dropdown arrow, it opens the modal anyway. Use force=True.
                         await btn.click(force=True)
            except: pass

            # Кликаем по контейнеру или инпуту внутри (Шаг 1 -> 2)
            input_trigger = container.locator('input').first
            if await input_trigger.count() == 0: input_trigger = container
            
            print(f"Clicking {label} field to open modal...")
            # Ensure visible
            await container.scroll_into_view_if_needed()
            # Close stray modals from previous attempts
            try: 
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(0.2)
            except: 
                pass
            
            await input_trigger.click(force=True)

            # 2. Ждем и находим поле поиска в модалке (Шаг 2-3)
            # Ищем input с placeholder "Search..." или "Найти..."
            # Он должен быть виден и активен.
            print("Waiting for modal search input...")
            search_input = None
            
            # Попытка найти активный инпут (часто фокус ставится сам)
            try:
                # Подождем чуть-чуть появления модалки
                await asyncio.sleep(0.5)
                # Ищем инпут внутри диалога
                # Селектор диалога в Material UI / React часто [role="dialog"]
                modal = self.page.locator('[role="dialog"], [class*="MuiDialog"]').first
                if await modal.count() > 0 and await modal.is_visible():
                     search_input = modal.locator('input[type="text"]').first
            except: pass

            # Если через диалог не нашли, ищем глобально видимый инпут (кроме основного, который мы кликнули)
            if not search_input or not await search_input.count():
                 search_input = self.page.locator('input[placeholder*="Search"], input[placeholder*="Найти"]').locator("visible=true").last

            if not search_input or await search_input.count() == 0:
                 print("(!) Search input in modal not found!")
                 return

            # 3. Вводим значение (Шаг 3)
            print(f"Typing '{value}' into modal...")
            try:
                await search_input.click(force=True)
            except: pass
            
            await search_input.press("Control+A")
            await search_input.press("Backspace")
            await search_input.press_sequentially(value, delay=50) 
            # Задержка 50мс - эмуляция человека, React успевает отработать

            # 4. Выбор из списка (Шаги 4-5)
            # "появляется поле с динамически меняющимся списком... фильтрующимся..."
            # "выбрать кнопку с максимальной информацией"
            
            print("Waiting for suggestions...")
            # Список обычно имеет role="listbox" или содержит items с role="option"
            # Также Trans.eu использует data-ctx="option" (или подобное)
            # Мы ищем ВСЕ опции.
            
            suggestions_locator = self.page.locator('[role="option"], [data-ctx="option"], li[class*="suggestion"], div[class*="MuiListItem-root"]')
            
            # Ждем появления хотя бы одной опции
            try:
                await suggestions_locator.first.wait_for(state="visible", timeout=3000)
            except:
                print("No standard suggestions found.")
            
            count = await suggestions_locator.count()
            if count == 0:
                 print("Zero suggestions found. Pressing Enter as fallback.")
                 await search_input.press("Enter")
            else:
                 # Алгоритм "Максимальной информации" (Шаг 4)
                 # Ищем опцию с самым длинным текстом, содержащую наш запрос
                 best_option = None
                 max_len = -1
                 search_query = value.split(",")[0].strip().lower() # "DE" or "Zurich"

                 print(f"Analyzing {count} suggestions...")
                 for i in range(count):
                     opt = suggestions_locator.nth(i)
                     if not await opt.is_visible(): continue
                     
                     text = await opt.inner_text()
                     text_lower = text.lower()
                     
                     # Игнорируем технические надписи
                     if "press space" in text_lower: continue

                     # Проверяем релевантность
                     # Если ввели "DE", "Germany (DE)" подходит.
                     # Если ввели "CH, 8048", "CH, 8048 Zurich..." подходит.
                     
                     if search_query in text_lower:
                         if len(text) > max_len:
                             max_len = len(text)
                             best_option = opt
                 
                 if best_option:
                     txt = await best_option.inner_text()
                     print(f"Selected best option (Max Info): '{txt}'")
                     
                     # 5. Клик (Шаг 5)
                     # "Фокусируюсь и кликаю... выпадающий список и модальное поле закрываются"
                     # Никаких Confirm кнопок!
                     await best_option.click(force=True)
                     print("Clicked best option. Modal should close automatically.")
                 else:
                     print("No relevant suggestion found via Max Info. Pressing Enter.")
                     await search_input.press("Enter")
            
            # 6. Ждем закрытия модалки (Шаг 6)
            await asyncio.sleep(1.0)
            
            # 7-9. Радиус (Шаги 8-9)
            # Always try to find radius selector if it appears
            # Look for ANY visible button/element containing "km" and "+" inside the filter area
            print("Checking for Radius selector (+ X km)...")
            
            # Broad locator: text containing "+ ... km"
            # Use a slightly loose regex to catch variations like "+0 km", "+ 0km", etc.
            radius_btn = self.page.locator('div, button, span').filter(has_text=re.compile(r'\+\s*\d+\s*km')).locator("visible=true").first
            
            if await radius_btn.count() > 0:
                print(f"Found radius selector: {await radius_btn.inner_text()}")
                await radius_btn.click()
                # Wait for dropdown
                plus_75 = self.page.locator('li, div[role="option"]').filter(has_text="+ 75 km").first
                if await plus_75.count() > 0 and await plus_75.is_visible():
                    await plus_75.click()
                    print("Radius set to +75 km.")
                else:
                    print("Option +75 km not found in radius dropdown.")
            else:
                print("Radius selector not found (no visible '+ ... km' element).")

        except Exception as e:
            print(f"Error setting location {label}: {e}")
            try:
                await self.page.keyboard.press("Escape")
            except:
                pass




    async def _set_dates(self, label: str, d_from: str, d_to: str):
        """Установка диапазона дат (Шаги 13-15) с обходом readonly."""
        if not d_from and not d_to: return

        print(f"Setting dates for {label}: {d_from} - {d_to}")
        try:
             # Ищем по лейблу
            label_el = self.page.get_by_text(re.compile(label, re.I)).first
            
            visible_inputs = []
            if await label_el.count() > 0:
                 container = label_el.locator("xpath=../..") 
                 inputs = container.locator("input:visible").all()
                 visible_inputs = await inputs

            # Fallback to placeholders if no inputs found by label
            if len(visible_inputs) < 2:
                print(f"Label-based date search failed for {label}. Trying placeholders...")
                date_inputs = self.page.locator("input[placeholder*='mm.yyyy'], input[placeholder*='мм.гггг']").all()
                all_visible = [inp for inp in await date_inputs if await inp.is_visible()]
                
                # Heuristic mapping
                if len(all_visible) >= 4:
                     if "loading" in label.lower() or "загрузки" in label.lower():
                         visible_inputs = all_visible[:2]
                     else:
                         visible_inputs = all_visible[2:4]
                elif len(all_visible) >= 2 and ("loading" in label.lower() or "загрузки" in label.lower()):
                     visible_inputs = all_visible[:2]

            if len(visible_inputs) >= 2:
                # Remove readonly via JS and fill
                async def fill_date(inp, val):
                    if not val: return
                    try:
                        # JS Hack: Remove readonly - USE locator.evaluate
                        await inp.evaluate("el => el.removeAttribute('readonly')")
                        # Clear and fill
                        await inp.click(force=True)
                        await inp.fill(val)
                        await inp.press("Enter")
                        # Close calendar if popped up
                        await self.page.keyboard.press("Escape") 
                    except Exception as e:
                        print(f"Error filling date {val}: {e}")

                if d_from: await fill_date(visible_inputs[0], d_from)
                if d_to: await fill_date(visible_inputs[1], d_to)
            else:
                print(f"(!) Could not find date inputs for {label}.")

        except Exception as e:
            print(f"Error setting dates {label}: {e}")

    async def _click_search_button(self):
        """Шаг 17: Зеленая кнопка Поиск."""
        print("Clicking search...")
        try:
            # Ищем кнопку по тексту или роли
            # Обычно это "Search" / "Поиск"
            btn = self.page.get_by_role("button", name=re.compile(r"Search|Поиск|Szukaj|Find", re.I)).last 
            # .last часто лучше, т.к. первая может быть в хедере
            
            if await btn.count() > 0:
                await btn.click()
                print("Clicked named search button.")
            else:
                 # Fallback: generic submit
                 await self.page.locator('button[type="submit"]').first.click()
                 print("Clicked generic submit button.")
            
            # Ждем результатов
            try:
                await self.page.wait_for_load_state("networkidle", timeout=10000)
            except: pass
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Error clicking search: {e}")

    async def _parse_freight_list(self) -> List[Dict]:
        """Parsing results with DETAILS (clicking each row)."""
        print("Parsing results with DETAILS...")
        
        # Основной контейнер строк
        rows = self.page.locator('[data-ctx="row"]')
        if await rows.count() == 0:
             rows = self.page.locator('div[role="row"]')
        
        count = await rows.count()
        print(f"Found {count} rows. Starting detailed scrape...")
        
        items = []
        # Limit to 50 to avoid infinite loops, but user wants full data.
        # We process them one by one.
        for i in range(min(count, 50)): 
            try:
                # Re-locate row to avoid stale element (though nth is usually safe)
                row = rows.nth(i)
                if not await row.is_visible(): continue
                
                # 1. Parse visible row (basic info)
                # We do this first to have a fallback if detail click fails
                text = await row.inner_text()
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                item = self._extract_data_from_text_lines(lines, text)
                if not item: continue
                
                # 2. Click for details
                # Click the first cell/text content (safer than row container)
                target = row.locator("div, span, td").first
                await target.click(force=True)
                
                # 3. Wait/Extract
                # Modal usually opens fast.
                await asyncio.sleep(0.5)
                
                details = await self._extract_details_from_page()
                item.update(details)
                
                # 4. Close modal
                # Escape is standard
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(0.2) # Animation
                
                items.append(item)
                
            except Exception as e:
                print(f"Error parsing row {i}: {e}")
                # Try to recover
                try: await self.page.keyboard.press("Escape")
                except: pass
                
        return items

    async def _extract_details_from_page(self) -> Dict:
        """
        Scrapes detailed info from the currently open modal/side-panel.
        Looking for: Body type, Capacity, LDM, Payment terms, Additional description.
        """
        data = {
            "body_type": None,
            "capacity": None,
            "ldm": None,
            "payment_terms": None,
            "additional_description": None,
            "price_details": None # e.g. "200 EUR 55 days"
        }
        
        try:
            # Get full text of the page (or specifically the modal if we could identify it)
            # Since modal covers screen, body text usually includes it.
            # But focusing on the generic 'dialog' role is better.
            content = self.page.locator('[role="dialog"], [class*="modal"], [class*="drawer"]').last
            if await content.count() > 0 and await content.is_visible():
                text = await content.inner_text()
            else:
                # Fallback checking <body> if modal not found by role
                text = await self.page.locator("body").inner_text()
            
            # Helper to find value by label using Regex
            # Labels: "Body type", "Capacity", "Dimensions", "Payment", "Description"
            
            text_lower = text.lower()
            
            # Body Type
            # E.g. "Body type\nCurtain" or "Body type: Curtain"
            # Regex looking for "Body type" followed by newline or colon
            # Note: English labels
            body_match = re.search(r'(?:Body type|Type of body)[\s:]+([^\n]+)', text, re.I)
            if body_match: data["body_type"] = body_match.group(1).strip()
            
            # Capacity / Weight
            # "Capacity: 24 t"
            cap_match = re.search(r'(?:Capacity|Weight)[\s:]+([^\n]+)', text, re.I)
            if cap_match: data["capacity"] = cap_match.group(1).strip()
            
            # LDM
            # "Dimensions: ... 13.6 ldm" or just "13.6 ldm"
            ldm_match = re.search(r'(\d+[.,]?\d*)\s*ldm', text, re.I)
            if ldm_match: data["ldm"] = ldm_match.group(1).strip()
            
            # Payment terms
            # "Payment: 45 days" or "Term: 60 days"
            pay_match = re.search(r'(?:Payment terms|Payment term|Payment)[\s:]+([^\n]+)', text, re.I)
            if pay_match: data["payment_terms"] = pay_match.group(1).strip()
            
            # Additional description
            # Improved Regex: Capture until next Capitalized Header or End of String
            # \W+ consumes colons, spaces, newlines.
            desc_match = re.search(r'Additional description\W+([\s\S]+?)(?=\n[A-Z][a-z]+|\Z)', text, re.I)
            if desc_match: 
                data["additional_description"] = desc_match.group(1).strip()
            else:
                # Fallback: specific "Comments" or similar
                desc_match_2 = re.search(r'(?:Remarks|Comments)\W+([\s\S]+?)(?=\n[A-Z][a-z]+|\Z)', text, re.I)
                if desc_match_2:
                     data["additional_description"] = desc_match_2.group(1).strip()
                else:
                     if len(text) > 50:
                         print(f"[DEBUG] Modal text snippet: {text[:200].replace(chr(10), ' ')}...")
            
            # Price Offer construction (User wants: Price + Date of payment)
            # We have price in basic info (data["price_original"]).
            # Here we just grab terms.
            # If we find specific "Date of payment" label.
            
        except Exception as e:
            print(f"Detail extraction error: {e}")
            
        return data

    def _extract_data_from_text_lines(self, lines, raw_text):
        """Парсинг строки (без изменений)."""
        place_pattern = re.compile(r'^([A-Z]{2})\s+(\d+(?:-\d+)?)\s+(.+)$')
        
        loading_place = "N/A"
        unloading_place = "N/A"
        loading_date = "N/A"
        unloading_date = "N/A"
        distance = "N/A"
        price = "N/A"
        currency = "EUR"
        
        place_indices = []
        for i, line in enumerate(lines):
            if place_pattern.match(line):
                place_indices.append(i)
                
        if len(place_indices) >= 2:
            loading_place = lines[place_indices[0]]
            unloading_place = lines[place_indices[1]]
            if place_indices[0] + 1 < len(lines): loading_date = lines[place_indices[0] + 1]
            if place_indices[1] + 1 < len(lines): unloading_date = lines[place_indices[1] + 1]
        else:
             if len(lines) > 0: loading_place = lines[0]
             for i, line in enumerate(lines[1:], 1):
                if re.match(r'^[A-Z]{2}\s', line):
                    unloading_place = line
                    if i+1 < len(lines): unloading_date = lines[i+1]
                    break
        
        currencies = ["EUR", "USD", "PLN", "GBP", "€", "$"]
        for line in lines:
            for curr in currencies:
                if curr in line:
                    if any(c.isdigit() for c in line):
                         price = line
                         currency = curr.replace("€", "EUR").replace("$", "USD")
                    elif "-" in line: price = "Negotiable"
                    break
            if price != "N/A": break
            
        cargo_info_parts = []
        for line in lines:
            if "km" in line and "N/A" in distance:
                 match = re.search(r'(\d+)\s?km', line)
                 if match: distance = match.group(1)
                 cargo_info_parts.append(line)
            elif " t," in line or " ldm" in line:
                 cargo_info_parts.append(line)
                 
        cargo_info = ", ".join(cargo_info_parts) if cargo_info_parts else "Details in raw text"
        unique_string = f"{loading_place}|{unloading_place}|{loading_date}|{price}|{raw_text[:20]}"
        content_hash = hashlib.md5(unique_string.encode()).hexdigest()[:12]
        
        return {
            "trans_id": f"gen_{content_hash}",
            "raw_text": raw_text,
            "loading_place": loading_place,
            "loading_date": loading_date,
            "unloading_place": unloading_place,
            "unloading_date": unloading_date,
            "cargo_info": cargo_info,
            "price_original": price,
            "currency": currency,
            "distance_km": int(distance) if distance.isdigit() else None
        }
