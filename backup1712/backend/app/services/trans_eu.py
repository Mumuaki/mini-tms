import asyncio
import re
import hashlib
import traceback
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable, Any
from playwright.async_api import Page, Locator

# --- Configuration & Selectors ---
class TransEuSelectors:
    # URL
    OFFERS_URL = "https://platform.trans.eu/exchange/offers"
    
    # Filter Panel
    LOADING_CTX = '[data-ctx="place-loading_place-0"]'
    UNLOADING_CTX = '[data-ctx="place-unloading_place-0"]'
    EXPAND_BTNS = ["Expand filters", "More filters", "Rozwiń filtry", "Развернуть фильтры", "Filters"]
    
    # Dates
    LOADING_DATE_LABEL = re.compile(r"Loading date|Дата загрузки", re.I)
    UNLOADING_DATE_LABEL = re.compile(r"Unloading date|Дата выгрузки", re.I)
    
    # Weight
    WEIGHT_LABEL = re.compile(r"Weight \(t\)|Вес \(т\)|Ciężar \(t\)", re.I)

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
    Implmenetation of User Scenario (Dec 2025).
    """

    def __init__(self, page: Page = None):
        self.page = page

    # --- Core Stability Methods ---

    async def _retry(self, action: Callable[[], Any], max_retries: int = 3, delay: float = 1.0) -> Any:
        last_exception = None
        for i in range(max_retries):
            try:
                return await action()
            except Exception as e:
                last_exception = e
                print(f"[Retry {i+1}] {e}. Waiting {delay}s...")
                await asyncio.sleep(delay)
        raise last_exception

    async def _human_delay(self, min_s: float = 0.3, max_s: float = 0.7):
        await asyncio.sleep(random.uniform(min_s, max_s))

    # --- Workflow ---

    async def ensure_on_search_page(self):
        if "exchange/offers" not in self.page.url:
            print(f"Navigating to {TransEuSelectors.OFFERS_URL}...")
            await self.page.goto(TransEuSelectors.OFFERS_URL, wait_until="domcontentloaded", timeout=60_000)
            await self._wait_for_main_content()
        else:
            print("Already on offers page.")

    async def _wait_for_main_content(self):
        print("Waiting for application readiness...")
        try:
            # 1. Close drawers
            if "drawer" in self.page.url or "details" in self.page.url:
                print("Closing open drawer...")
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(0.5)

            # 2. Expand filters if needed
            loading_input = self.page.locator(TransEuSelectors.LOADING_CTX).first
            if not await loading_input.is_visible():
                print("Filters collapsed. Expanding...")
                await self._ensure_filters_expanded()
                await asyncio.sleep(1.0)

            # 3. Wait for filters
            await self.page.wait_for_selector(TransEuSelectors.LOADING_CTX, timeout=20_000, state='visible')
        
        except Exception:
            # Reload strategy
            if "exchange/offers" in self.page.url:
                 print("Reloading page...")
                 await self.page.reload()
                 await asyncio.sleep(3)
                 await self._ensure_filters_expanded()

    async def search_freights(self, filters: Optional[Dict] = None) -> List[Dict]:
        await self.ensure_on_search_page()
        await self._wait_for_main_content()

        if filters:
            await self._apply_filters(filters)

        return await self._parse_freight_list()

    async def _apply_filters(self, filters: Dict):
        print(f"Applying filters: {filters}")
        # Reset view
        await self.page.evaluate("window.scrollTo(0, 0)")
        
        # 1. Locations (Steps 1-9)
        # 1. Locations (Steps 1-9)
        # Always attempt to set (or clear) locations
        await self._retry(lambda: self._set_location("Загрузка", TransEuSelectors.LOADING_CTX, filters.get("origin")))
        await self._retry(lambda: self._set_location("Разгрузка", TransEuSelectors.UNLOADING_CTX, filters.get("destination")))

        # 2. Expand Filters (Step 10)
        await self._ensure_filters_expanded()

        # 3. Dates (Steps 11-15) - Default Logic applied here
        l_from = filters.get("loading_date_from")
        l_to = filters.get("loading_date_to")
        u_from = filters.get("unloading_date_from")
        u_to = filters.get("unloading_date_to")
        
        # Apply defaults if missing (Step 14)
        today = datetime.now()
        if not l_to: 
            l_to = today.strftime("%d.%m.%Y")
        
        # Next workday logic for unloading (simplistic +1 day for now)
        if not u_to:
            next_day = today + timedelta(days=1)
            # Skip weekend logic could be added here
            u_to = next_day.strftime("%d.%m.%Y")

        await self._set_dates("Loading date", l_from, l_to)
        await self._set_dates("Unloading date", u_from, u_to)

        # 4. Weight (Step 16)
        # 4. Weight (Step 16)
        # Default max weight to 24.0t if not specified (Standard truck)
        max_w = filters.get("max_weight")
        if max_w:
             # Convert kg to tons if > 100, assumption is input might be kg
             if max_w > 100: max_w = max_w / 1000.0
             await self._set_weight(max_w)

        # 5. Search (Step 17)
        await self._click_search_button()

    # --- Location Logic (Steps 1-9) ---

    async def _set_location(self, label: str, ctx_selector: str, value: str):
        print(f"Setting {label}: {value}")

        container = self.page.locator(ctx_selector).first
        await container.scroll_into_view_if_needed()
        
        # Clear existing
        try:
           # Check for clear button (usually an 'X' icon button)
           clear_btn = container.locator("button").first
           if await clear_btn.is_visible(): 
               await clear_btn.click()
               await self._human_delay(0.2)
        except: pass
        
        if not value: 
            return # Field cleared, stop here.
        

        
        # Open Modal
        await container.click(force=True)

        # Search in Modal
        if not await self._search_in_modal(value):
             # Retry click
             await container.click(force=True)
             if not await self._search_in_modal(value):
                 print(f"Failed to open modal for {label}")
                 return

        # Select Best (Max Info)
        await self._select_best_suggestion(value)
        
        # Radius (Steps 8-9)
        # Check actual updated value in the input to decide on radius
        # Requirement: "Country (2 chars) + Index + Place Name"
        try:
            # Read value from input (or text content if not input)
            inp = container.locator('input').first
            if await inp.count() > 0:
                final_val = await inp.input_value()
            else:
                final_val = await container.inner_text()
            
            # Pattern: 2 letters start, then somewhere digits, then somewhere letters (place)
            # Regex: ^[A-Za-z]{2}.*\d+.*[A-Za-z]+
            is_full_address = re.search(r'^[A-Za-z]{2}.*\d+.*[A-Za-z]+', final_val.strip())
            
            if is_full_address:
                 print(f"Detected full address '{final_val}'. Setting radius...")
                 await self._try_set_radius()
            else:
                 print(f"Address '{final_val}' seems generic. Skipping radius.")
                 
        except Exception as e:
            print(f"Radius check error: {e}")
        
        await self._safe_escape() # Ensure closed

    async def _search_in_modal(self, value: str) -> bool:
        try:
            # Wait for modal generic wrapper
            await self.page.locator(TransEuSelectors.MODAL_DIALOG).first.wait_for(timeout=3000)
            
            # Find input
            inp = self.page.locator(f'{TransEuSelectors.MODAL_DIALOG} input[type="text"]').first
            if not await inp.count() or not await inp.is_visible():
                # Fallback global search input
                inp = self.page.locator('input[placeholder*="Search"], input[placeholder*="Найти"]').locator("visible=true").last
            
            if await inp.count() > 0:
                await inp.click(force=True)
                await inp.fill(value)
                await self._human_delay(0.3, 0.6)
                return True
            return False
        except: return False

    async def _select_best_suggestion(self, input_value: str):
        suggestions = self.page.locator(TransEuSelectors.SUGGESTION_ITEMS)
        try:
            await suggestions.first.wait_for(state="visible", timeout=4000)
        except:
            await self.page.keyboard.press("Enter")
            return

        count = await suggestions.count()
        if count == 0:
             await self.page.keyboard.press("Enter")
             return

        # Step 4: Max Info Selection
        best_option = None
        max_len = -1
        search_query = input_value.split(",")[0].strip().lower()

        for i in range(count):
            opt = suggestions.nth(i)
            text = await opt.inner_text()
            text_lower = text.lower()
            
            if "press space" in text_lower: continue

            if search_query in text_lower:
                if len(text) > max_len:
                    max_len = len(text)
                    best_option = opt
        
        if best_option:
            print(f"Selected (Max Info): '{await best_option.inner_text()}'")
            await best_option.scroll_into_view_if_needed()
            await best_option.click(force=True)
        else:
            await self.page.keyboard.press("Enter")
        
        await self._human_delay()

    async def _try_set_radius(self):
        """Sets radius to +75 km if selector is available."""
        try:
            # Look for radius button near the active input context
            # We use a broad search because it appears dynamically
            radius_btn = self.page.locator('div, button, span').filter(has_text=TransEuSelectors.RADIUS_BTN_PATTERN).locator("visible=true").first
            
            # Short wait as it should appear immediately after selection
            try: await radius_btn.wait_for(timeout=2000)
            except: pass

            if await radius_btn.count() > 0:
                print("Setting radius +75 km...")
                await radius_btn.click()
                option = self.page.locator('li, div[role="option"]').filter(has_text=TransEuSelectors.RADIUS_OPTION_75).first
                if await option.count() > 0:
                    await option.click()
        except: pass

    # --- Dates & Weight (Steps 10-16) ---
    
    async def _set_dates(self, label_part: str, d_from: str, d_to: str):
        if not d_from and not d_to: return
        print(f"Setting dates {label_part}: {d_from} - {d_to}")
        
        try:
            inputs = await self._find_inputs_by_label(label_part)
            # Expecting 2 inputs: From (left) and To (right)
            # Step 14: Default is both right fields filled.
            
            if len(inputs) >= 2:
                # If only one date provided, logic depends.
                # Usually we want specific date -> set 'To' (right field) as per instruction?
                # Instruction says: "По умолчанию должны быть заполнены оба правых поля"
                # So we prioritize the second input (index 1)
                
                if d_from: await self._fill_date_smart(inputs[0], d_from)
                if d_to: await self._fill_date_smart(inputs[1], d_to)
            elif len(inputs) == 1 and d_to:
                 await self._fill_date_smart(inputs[0], d_to)

        except Exception as e:
            print(f"Date error {label_part}: {e}")

    async def _set_weight(self, max_weight: float):
        """Step 16: Set Weight To = 0.9"""
        print(f"Setting Weight (t) To: {max_weight}")
        try:
             # Find Weight inputs
             # Regex for label
             label = self.page.get_by_text(TransEuSelectors.WEIGHT_LABEL).first
             if await label.count() > 0:
                 inputs = await label.locator("xpath=../..").locator("input:visible").all()
                 if len(inputs) >= 2:
                     # Right field is 'To'
                     inp_to = inputs[1]
                     # Check if empty or fill
                     await inp_to.fill(str(max_weight))
                     await inp_to.press("Enter")
        except Exception as e:
            print(f"Weight set error: {e}")

    async def _find_inputs_by_label(self, label_text: str) -> List[Locator]:
        # Try both regex and string
        try:
             label = self.page.get_by_text(re.compile(label_text, re.I)).first
             if await label.count():
                  return await label.locator("xpath=../..").locator("input:visible").all()
        except: pass
        return []

    async def _fill_date_smart(self, inp: Locator, value: str):
        # JS Hack to remove readonly if present (Step 15 mentioned calendar click, 
        # but typing + Enter is usually faster and more reliable if allowed)
        # We try typing first.
        try:
            await inp.evaluate("el => el.removeAttribute('readonly')")
            await inp.click(force=True)
            await inp.fill(value)
            await inp.press("Enter")
            await self._safe_escape() # Close calendar if popped
        except: pass

    # --- Search ---

    async def _ensure_filters_expanded(self):
        for label in TransEuSelectors.EXPAND_BTNS:
            btn = self.page.get_by_role("button", name=re.compile(label, re.I)).first
            if await btn.is_visible():
                await btn.click()
                await self._human_delay()
                return

    async def _click_search_button(self):
        print("Clicking search (Step 17)...")
        btn = self.page.get_by_role("button", name=TransEuSelectors.SEARCH_BTN_PATTERN).last
        if await btn.count() == 0:
            btn = self.page.locator('button[type="submit"]').first
        
        await btn.click()
        try: await self.page.wait_for_load_state("networkidle", timeout=8000)
        except: pass
        await self._human_delay(1.5, 2.5)

    # --- Parsing ---
    
    async def _parse_freight_list(self) -> List[Dict]:
        rows = self.page.locator(TransEuSelectors.ROW_CTX)
        try: await rows.first.wait_for(state="visible", timeout=5000)
        except: print("No rows found.")
        
        count = await rows.count()
        print(f"Found {count} items.")
        items = []
        
        for i in range(min(count, 50)):
            try:
                row = rows.nth(i)
                if not await row.is_visible(): continue
                
                text = await row.inner_text()
                item = self._parse_basic_row_text(text)
                if not item: continue
                
                # Details
                await row.locator("div, span, td").first.click(force=True)
                details = await self._extract_detailed_info()
                item.update(details)
                await self._safe_escape()
                await self._human_delay(0.2, 0.4)
                items.append(item)
            except: 
                await self._safe_escape()
                
        return items

    def _parse_basic_row_text(self, text: str) -> Optional[Dict]:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if not lines: return None
        data = {"loading_place": "N/A", "unloading_place": "N/A", "price_original": "N/A", "currency": "EUR", "trans_id": ""}
        
        # Regex for Places
        place_pattern = re.compile(r'^([A-Z]{2})\s+(\d+(?:-\d+)?)\s+(.+)$')
        places = [l for l in lines if place_pattern.match(l)]
        if len(places) >= 2:
            data["loading_place"] = places[0]
            data["unloading_place"] = places[1]
            try:
                p1 = lines.index(places[0])
                p2 = lines.index(places[1])
                if p1 + 1 < len(lines): data["loading_date"] = lines[p1+1]
                if p2 + 1 < len(lines): data["unloading_date"] = lines[p2+1]
            except: pass

        for line in lines:
             if any(c in line for c in ["EUR", "USD", "PLN", "€", "$"]) and any(d.isdigit() for d in line):
                 data["price_original"] = line
                 break
                 
        # Parse Weight
        # Look for pattern: number + " t" or " kg"
        w_match = re.search(r'(\d+[.,]?\d*)\s*(t|kg|T|KG)', text)
        if w_match:
             data["cargo_info"] = w_match.group(0) # e.g. "24 t"
             data["weight_kg"] = self._parse_weight_to_kg(w_match.group(0))

        unique = f"{data['loading_place']}|{data['unloading_place']}|{data['price_original']}|{random.randint(0,9999)}"
        data["trans_id"] = f"gen_{hashlib.md5(unique.encode()).hexdigest()[:12]}"
        data["raw_text"] = text
        return data

    def _parse_weight_to_kg(self, text: str) -> Optional[float]:
        try:
            val_match = re.search(r'(\d+[.,]?\d*)', text)
            if not val_match: return None
            val = float(val_match.group(1).replace(',', '.'))
            
            if 'kg' in text.lower():
                return val
            if 't' in text.lower():
                return val * 1000.0
            return val # Default assumption?
        except: return None

    async def _extract_detailed_info(self) -> Dict:
        data = {k: None for k in ["body_type", "capacity", "ldm", "payment_terms", "additional_description"]}
        try:
            content = self.page.locator(TransEuSelectors.DETAIL_MODAL).last
            try: await content.wait_for(state="visible", timeout=2000)
            except: content = self.page.locator("body")
            text = await content.inner_text()
            
            data["body_type"] = self._regex_val(r'(?:Body type|Type of body)[\s:]+([^\n]+)', text)
            data["capacity"] = self._regex_val(r'(?:Body type|Type of body)[\s:]+([^\n]+)', text) # typo fixed
            data["ldm"] = self._regex_val(r'(\d+[.,]?\d*)\s*ldm', text)
            
            desc_match = re.search(r'Additional description\W+([\s\S]+?)(?=\n[A-Z][a-z]+|\Z)', text, re.I)
            if desc_match: data["additional_description"] = desc_match.group(1).strip()
        except: pass
        return data

    def _regex_val(self, p, t):
        m = re.search(p, t, re.I)
        return m.group(1).strip() if m else None

    async def _safe_escape(self):
        try: await self.page.keyboard.press("Escape")
        except: pass
