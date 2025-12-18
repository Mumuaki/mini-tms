import asyncio
import re
import hashlib
import traceback
from typing import List, Dict, Optional
from playwright.async_api import Page, Locator

# --- Configuration & Selectors ---
class TransEuSelectors:
    # URL
    OFFERS_URL = "https://platform.trans.eu/exchange/offers"
    
    # Filter Panel
    LOADING_CTX = '[data-ctx="place-loading_place-0"]'
    UNLOADING_CTX = '[data-ctx="place-unloading_place-0"]'
    EXPAND_BTNS = ["Expand filters", "More filters", "Rozwiń filtry", "Развернуть фильтры", "Filters"]
    
    # Modals
    MODAL_DIALOG = '[role="dialog"], [class*="MuiDialog"]'
    MODAL_SEARCH_INPUT = 'input[type="text"]' # inside modal
    SUGGESTION_ITEMS = '[role="option"], [data-ctx="option"], li[class*="suggestion"], div[class*="MuiListItem-root"]'
    
    # Radius
    RADIUS_BTN_PATTERN = re.compile(r'\+\s*\d+\s*km')
    RADIUS_OPTION_75 = "+ 75 km"

    # Search
    SEARCH_BTN_PATTERN = re.compile(r"Search|Поиск|Szukaj|Find", re.I)
    
    # Results
    ROW_CTX = '[data-ctx="row"]'
    ROW_FALLBACK = 'div[role="row"]'
    
    # Details
    DETAIL_MODAL = '[role="dialog"], [class*="modal"], [class*="drawer"]'


class TransEuScraper:
    """
    Сервис для работы со страницей поиска грузов Trans.eu.
    Оптимизирован под реальный UI Trans.eu (React, Shadow DOM, Modal behavior).
    """

    def __init__(self, page: Page = None):
        self.page = page

    async def ensure_on_search_page(self):
        """Проверка, что мы на странице поиска грузов."""
        if "exchange/offers" not in self.page.url:
            print(f"Navigating to {TransEuSelectors.OFFERS_URL}...")
            await self.page.goto(TransEuSelectors.OFFERS_URL, wait_until="domcontentloaded", timeout=60_000)
            # Give SPA a moment to hydrate
            await asyncio.sleep(2)
        else:
            print("Already on offers page.")

    async def search_freights(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Основной флоу: Проверка -> Фильтры -> Парсинг.
        """
        await self.ensure_on_search_page()
        await self._wait_for_main_content()

        if filters:
            await self._apply_filters(filters)

        return await self._parse_freight_list()

    async def _wait_for_main_content(self):
        try:
            print("Waiting for freight list container...")
            # Wait for the actual filter input to be visible, ensuring the SPA is fully ready
            await self.page.wait_for_selector(TransEuSelectors.LOADING_CTX, timeout=20_000, state='visible')
        except Exception as e:
            print(f"Warning: Main content (filters) wait timeout: {e}")
            print(f"Current URL: {self.page.url}")
            if "login" in self.page.url:
                print("(!) Redirected to Login page. Please log in manually in the browser window.")
                raise Exception("User not logged in")

    async def _apply_filters(self, filters: Dict):
        """Применение всех фильтров."""
        print(f"Applying filters: {filters}")
        
        # Reset view
        try: await self.page.evaluate("window.scrollTo(0, 0)")
        except: pass

        # 1. Locations
        if "origin" in filters:
            await self._set_location("Загрузка", TransEuSelectors.LOADING_CTX, filters["origin"])
        
        if "destination" in filters:
            await self._set_location("Разгрузка", TransEuSelectors.UNLOADING_CTX, filters["destination"])

        # 2. Expand for Dates/Rest
        await self._ensure_filters_expanded()

        # 3. Dates
        if filters.get("loading_date_from") or filters.get("loading_date_to"):
            await self._set_dates("Loading date", filters.get("loading_date_from"), filters.get("loading_date_to"))
            
        if filters.get("unloading_date_from") or filters.get("unloading_date_to"):
            await self._set_dates("Unloading date", filters.get("unloading_date_from"), filters.get("unloading_date_to"))

        # 4. Search
        await self._click_search_button()

    # --- Location Logic ---

    async def _set_location(self, label: str, ctx_selector: str, value: str):
        """Полный цикл установки локации: Открытие -> Поиск -> Выбор -> Радиус"""
        if not value: return

        print(f"Setting location '{label}' to '{value}'")
        try:
            container = self.page.locator(ctx_selector).first
            if await container.count() == 0:
                print(f"(!) Input container for {label} not found")
                return

            # 1. Open Modal
            if not await self._open_location_modal(container):
                return

            # 2. Search in Modal
            if not await self._search_in_modal(value):
                return

            # 3. Select Best Suggestion
            await self._select_best_suggestion(value)
            
            # 4. Radius (Only for Origin usually, but logic is generic)
            # Check if we should apply radius (Hardcoded +75km logic for now based on user flow)
            await self._try_set_radius()

        except Exception as e:
            print(f"Error setting location {label}: {e}")
            await self._safe_escape()

    async def _open_location_modal(self, container: Locator) -> bool:
        """Клик по полю для открытия модалки."""
        try:
            # Clear previous value if any clear button exists
            await self._clear_input_if_needed(container)
            
            # Click
            print("Opening location modal...")
            await container.scroll_into_view_if_needed()
            await self._safe_escape() # Close any stray modals
            
            await container.click(force=True)
            return True
        except Exception as e:
            print(f"Failed to open modal: {e}")
            return False

    async def _clear_input_if_needed(self, container: Locator):
        try:
            btns = container.locator("button").all()
            for btn in await btns:
                if await btn.is_visible():
                    await btn.click(force=True)
        except: pass

    async def _search_in_modal(self, value: str) -> bool:
        """Поиск и ввод текста в модальном окне."""
        print("Waiting for modal input...")
        # Wait for modal generic
        try:
            await self.page.wait_for_selector(TransEuSelectors.MODAL_DIALOG, timeout=2000)
        except: pass

        # Strategy 1: Input inside dialog
        search_input = self.page.locator(f'{TransEuSelectors.MODAL_DIALOG} input[type="text"]').first
        
        # Strategy 2: Global visible input
        if not await search_input.count() or not await search_input.is_visible():
            search_input = self.page.locator('input[placeholder*="Search"], input[placeholder*="Найти"]').locator("visible=true").last

        if await search_input.count() > 0:
            print(f"Typing '{value}'...")
            await search_input.fill(value)
            # Small delay for React
            await asyncio.sleep(0.1) 
            return True
        else:
            print("(!) Search input in modal not found!")
            return False

    async def _select_best_suggestion(self, input_value: str):
        """Выбор лучшей подсказки по длине текста."""
        print("Waiting for suggestions...")
        suggestions = self.page.locator(TransEuSelectors.SUGGESTION_ITEMS)
        
        try:
            await suggestions.first.wait_for(state="visible", timeout=3000)
        except:
            print("No suggestions found via wait.")

        count = await suggestions.count()
        if count == 0:
             print("Zero suggestions. Pressing Enter.")
             await self.page.keyboard.press("Enter")
             return

        # Algorithm: Max Length Match
        best_option = None
        max_len = -1
        search_query = input_value.split(",")[0].strip().lower()

        for i in range(count):
            opt = suggestions.nth(i)
            if not await opt.is_visible(): continue
            
            text = await opt.inner_text()
            text_lower = text.lower()
            
            if "press space" in text_lower: continue

            if search_query in text_lower:
                if len(text) > max_len:
                    max_len = len(text)
                    best_option = opt
        
        if best_option:
            print(f"Selected: '{await best_option.inner_text()}'")
            await best_option.click(force=True)
        else:
            print("No good match. Pressing Enter.")
            await self.page.keyboard.press("Enter")
        
        # Wait for close
        await asyncio.sleep(0.5)

    async def _try_set_radius(self):
        """Попытка установить радиус +75км."""
        print("Checking for Radius selector...")
        try:
            # Look for button like "+ 0 km" inside the active area
            # We assume the radius selector appears near the filled input
            radius_btn = self.page.locator('div, button, span').filter(has_text=TransEuSelectors.RADIUS_BTN_PATTERN).locator("visible=true").first
            
            if await radius_btn.count() > 0:
                await radius_btn.click()
                # Find +75 km option
                option = self.page.locator('li, div[role="option"]').filter(has_text=TransEuSelectors.RADIUS_OPTION_75).first
                if await option.count() > 0:
                    await option.click()
                    print("Radius set to +75 km.")
                else:
                    print("Option +75 km not found.")
        except Exception:
            pass

    # --- Date Logic ---

    async def _set_dates(self, label_part: str, d_from: str, d_to: str):
        if not d_from and not d_to: return
        print(f"Setting dates for {label_part}...")

        # Find inputs
        inputs = await self._find_date_inputs(label_part)
        if len(inputs) < 2:
            print(f"(!) Date inputs for {label_part} not found.")
            return

        for inp, val in zip(inputs, [d_from, d_to]):
            if val:
                await self._fill_date_input(inp, val)

    async def _find_date_inputs(self, label_part: str) -> List[Locator]:
        # Try finding by text label nearby
        label_el = self.page.get_by_text(re.compile(label_part, re.I)).first
        if await label_el.count() > 0:
            return await label_el.locator("xpath=../..").locator("input:visible").all()
        
        # Fallback: heuristics by placeholder position
        all_dates = await self.page.locator("input[placeholder*='mm.yyyy'], input[placeholder*='мм.гггг']").locator("visible=true").all()
        
        is_loading = "loading" in label_part.lower() or "загруз" in label_part.lower()
        if len(all_dates) >= 4:
            return all_dates[:2] if is_loading else all_dates[2:4]
        if len(all_dates) >= 2 and is_loading:
            return all_dates[:2]
        
        return []

    async def _fill_date_input(self, inp: Locator, value: str):
        try:
            # Hack: Remove readonly to allow typing
            await inp.evaluate("el => el.removeAttribute('readonly')")
            await inp.click(force=True)
            await inp.fill(value)
            await inp.press("Enter")
            await self._safe_escape()
        except Exception as e:
            print(f"Error filling date {value}: {e}")

    async def _ensure_filters_expanded(self):
        try:
            for label in TransEuSelectors.EXPAND_BTNS:
                btn = self.page.get_by_role("button", name=re.compile(label, re.I)).first
                if await btn.count() and await btn.is_visible():
                    print(f"Clicking '{label}'...")
                    await btn.click()
                    await asyncio.sleep(0.5)
                    return
        except: pass

    async def _click_search_button(self):
        print("Clicking search...")
        try:
            btn = self.page.get_by_role("button", name=TransEuSelectors.SEARCH_BTN_PATTERN).last
            if await btn.count() > 0:
                await btn.click()
            else:
                await self.page.locator('button[type="submit"]').first.click()
            
            try: await self.page.wait_for_load_state("networkidle", timeout=5000)
            except: pass
            await asyncio.sleep(2) # Final buffer for results
        except Exception as e:
            print(f"Search click error: {e}")

    # --- Parsing Logic ---

    async def _parse_freight_list(self) -> List[Dict]:
        """Парсинг списка с открытием деталей."""
        rows = self.page.locator(TransEuSelectors.ROW_CTX)
        if await rows.count() == 0:
            rows = self.page.locator(TransEuSelectors.ROW_FALLBACK)
        
        count = await rows.count()
        print(f"Found {count} rows. Scraping details...")
        
        items = []
        # Limit processing
        files_to_process = min(count, 50)
        
        for i in range(files_to_process):
            try:
                row = rows.nth(i)
                if not await row.is_visible(): continue
                
                # 1. Basic Text
                text = await row.inner_text()
                item = self._parse_basic_row_text(text)
                if not item: continue
                
                # 2. Click for Details
                await row.locator("div, span, td").first.click(force=True)
                
                # 3. Extract Details
                details = await self._extract_detailed_info()
                item.update(details)
                
                # 4. Close
                await self._safe_escape()
                await asyncio.sleep(0.2) # Animation buffer
                
                items.append(item)
            except Exception as e:
                print(f"Row {i} error: {e}")
                await self._safe_escape()
                
        return items

    def _parse_basic_row_text(self, text: str) -> Optional[Dict]:
        """Преобразование сырого текста строки в базовую структуру."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if not lines: return None
        
        # Regex for "DE 12345 City" validation
        place_pattern = re.compile(r'^([A-Z]{2})\s+(\d+(?:-\d+)?)\s+(.+)$')
        
        data = {
            "loading_place": "N/A", "unloading_place": "N/A",
            "loading_date": "N/A", "unloading_date": "N/A",
            "price_original": "N/A", "currency": "EUR",
            "distance_km": None, "raw_text": text
        }
        
        # Identify Places
        places = [l for l in lines if place_pattern.match(l)]
        if len(places) >= 2:
            data["loading_place"] = places[0]
            data["unloading_place"] = places[1]
            
            # Simple heuristic for dates (line after place)
            try:
                p1_idx = lines.index(places[0])
                if p1_idx + 1 < len(lines): data["loading_date"] = lines[p1_idx + 1]
                
                p2_idx = lines.index(places[1])
                if p2_idx + 1 < len(lines): data["unloading_date"] = lines[p2_idx + 1]
            except: pass
        
        # Identify Price
        for line in lines:
            if any(c in line for c in ["EUR", "USD", "PLN", "€", "$"]):
                 if any(d.isdigit() for d in line):
                     data["price_original"] = line
                     break
        
        # Generate ID
        unique = f"{data['loading_place']}|{data['unloading_place']}|{data['price_original']}"
        data["trans_id"] = f"gen_{hashlib.md5(unique.encode()).hexdigest()[:12]}"
        
        return data

    async def _extract_detailed_info(self) -> Dict:
        """Сбор детальной информации из открытого модального окна/панели."""
        data = {
            "body_type": None, "capacity": None, "ldm": None,
            "payment_terms": None, "additional_description": None
        }
        
        try:
            # Wait a tick for content
            await asyncio.sleep(0.3)
            
            # Find content container
            content = self.page.locator(TransEuSelectors.DETAIL_MODAL).last
            if not await content.count() or not await content.is_visible():
                content = self.page.locator("body") # Fallback
                
            text = await content.inner_text()
            
            # Regex Extraction
            data["body_type"] = self._regex_val(r'(?:Body type|Type of body)[\s:]+([^\n]+)', text)
            data["capacity"] = self._regex_val(r'(?:Capacity|Weight)[\s:]+([^\n]+)', text)
            data["ldm"] = self._regex_val(r'(\d+[.,]?\d*)\s*ldm', text)
            data["payment_terms"] = self._regex_val(r'(?:Payment terms|Payment term|Payment)[\s:]+([^\n]+)', text)
            
            # Additional Description (Complex)
            desc_match = re.search(r'Additional description\W+([\s\S]+?)(?=\n[A-Z][a-z]+|\Z)', text, re.I)
            if desc_match:
                 data["additional_description"] = desc_match.group(1).strip()
            
        except Exception as e:
            print(f"Details error: {e}")
            
        return data

    def _regex_val(self, pattern: str, text: str) -> Optional[str]:
        m = re.search(pattern, text, re.I)
        return m.group(1).strip() if m else None

    async def _safe_escape(self):
        try: await self.page.keyboard.press("Escape")
        except: pass
