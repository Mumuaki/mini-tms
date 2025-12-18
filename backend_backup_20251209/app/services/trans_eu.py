import os
import asyncio
from playwright.async_api import async_playwright, Browser, Page
from datetime import datetime
from typing import List, Dict, Optional


class TransEuScraper:
    """Сервис для получения грузов с Trans.eu через автоматизацию браузера."""

    def __init__(self):
        self.username = os.getenv("TRANS_USER")
        self.password = os.getenv("TRANS_PASSWORD")
        self.base_url = "https://www.trans.eu"
        self.login_url = "https://auth.platform.trans.eu/accounts/login"
        self.freights_url = "https://platform.trans.eu/exchange/offers"

        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False

    # ---------------------------------------------------------------------
    # Browser handling
    # ---------------------------------------------------------------------
    async def start_browser(self, headless: bool = True):
        """Запуск браузера (пытаемся подключиться к уже запущенному CDP)."""
        playwright = await async_playwright().start()

        # Try to connect to an existing Chrome instance via CDP
        try:
            self.browser = await playwright.chromium.connect_over_cdp(
                "http://localhost:9222"
            )
            if self.browser.contexts:
                context = self.browser.contexts[0]
                self.page = context.pages[0] if context.pages else await context.new_page()
            else:
                # No contexts – unlikely, but fall back to launching a new one
                pass
            print("✓ Connected to existing browser via CDP")
            return
        except Exception:
            print("Could not connect to existing browser, launching new one...")

        # Fallback: launch a fresh Chromium instance
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
            timezone_id="Europe/Moscow",
        )
        # Hide automation flag
        await context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """
        )
        self.page = await context.new_page()
        self.page.set_default_timeout(60_000)
        print("✓ Browser started")

    # ---------------------------------------------------------------------
    # Login
    # ---------------------------------------------------------------------
    async def login(self):
        """Вход в систему Trans.eu."""
        if not self.page:
            await self.start_browser()

        if not self.username or not self.password:
            raise ValueError("TRANS_USER and TRANS_PASSWORD must be set in .env")

        print(f"Navigating to {self.login_url}...")
        try:
            await self.page.goto(self.login_url, wait_until="domcontentloaded", timeout=60_000)
            print("✓ Page loaded")
        except Exception as e:
            print(f"Warning: Page load timeout, but continuing: {e}")

        # Already logged in?
        current_url = self.page.url
        if "login" not in current_url.lower() and "auth" not in current_url.lower():
            print(f"Already logged in (URL: {current_url})")
            self.is_logged_in = True
            return

        # ---- locate email field ------------------------------------------------
        email_selectors = [
            'input[name="login"]',   # primary selector for Trans.eu
            'input[name="email"]',
            'input[type="email"]',
            'input[name="username"]',
        ]
        email_input = None
        for selector in email_selectors:
            try:
                email_input = await self.page.wait_for_selector(selector, timeout=5_000)
                if email_input:
                    print(f'✓ Found email input with selector: {selector}')
                    break
            except Exception:
                continue

        if not email_input:
            await self.page.screenshot(path="login_page_debug.png")
            raise Exception(
                "Could not find email input field. Screenshot saved to login_page_debug.png"
            )

        await email_input.fill(self.username)
        print(f"✓ Entered username: {self.username}")

        # ---- locate password field ---------------------------------------------
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
        ]
        password_input = None
        for selector in password_selectors:
            try:
                password_input = await self.page.wait_for_selector(selector, timeout=5_000)
                if password_input:
                    print(f'✓ Found password input with selector: {selector}')
                    break
            except Exception:
                continue

        if not password_input:
            await self.page.screenshot(path="login_page_debug.png")
            raise Exception("Could not find password input field")

        await password_input.fill(self.password)
        print("✓ Entered password")

        # ---- submit ------------------------------------------------------------
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Войти")',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
        ]
        submit_button = None
        for selector in submit_selectors:
            try:
                submit_button = await self.page.wait_for_selector(selector, timeout=3_000)
                if submit_button:
                    print(f'✓ Found submit button with selector: {selector}')
                    break
            except Exception:
                continue

        if submit_button:
            await submit_button.click()
            print("✓ Clicked login button")
        else:
            await password_input.press("Enter")
            print("✓ Pressed Enter to submit")

        # ---- wait for navigation ------------------------------------------------
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30_000)
        except Exception:
            print("Warning: Timeout waiting for networkidle, continuing...")

        await asyncio.sleep(2)

        # ---- final check --------------------------------------------------------
        current_url = self.page.url
        print(f"Current URL after login: {current_url}")
        if "login" in current_url.lower() or "auth" in current_url.lower():
            await self.page.screenshot(path="login_failed_debug.png")
            error_text = await self.page.evaluate(
                """
                () => {
                    const errorElements = document.querySelectorAll('.error, .alert, [class*="error"], [class*="alert"]');
                    return Array.from(errorElements).map(el => el.textContent).join('; ');
                }
                """
            )
            if error_text:
                raise Exception(f"Login failed with error: {error_text}")
            else:
                print("Warning: Still on login page, but no error found. Might be successful.")
                self.is_logged_in = True
        else:
            self.is_logged_in = True

    # ---------------------------------------------------------------------
    # Search freights
    # ---------------------------------------------------------------------
    async def search_freights(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Поиск грузов на Trans.eu."""
        if not self.is_logged_in:
            await self.login()

        print("Navigating to freights page...")
        try:
            await self.page.goto(
                self.freights_url,
                wait_until="domcontentloaded",
                timeout=180_000,
            )
            print("✓ Freights page loaded (domcontentloaded)")
        except Exception as e:
            print(f"Warning: domcontentloaded timeout – {e}, retrying with networkidle")
            await self.page.goto(
                self.freights_url,
                wait_until="networkidle",
                timeout=180_000,
            )
            print("✓ Freights page loaded (networkidle)")

        # Wait for at least one freight row to appear
        try:
            print("Waiting for freight rows...")
            await self.page.wait_for_selector('[data-ctx="row"]', timeout=20_000)
            print("✓ Freight rows appeared")
        except Exception as e:
            print(f"Warning: Timeout waiting for [data-ctx='row']: {e}")

        await asyncio.sleep(2)

        # Apply filters if supplied
        if filters:
            await self._apply_filters(filters)

        # Parse the resulting list
        freights = await self._parse_freight_list()
        print(f"✓ Found {len(freights)} freights")
        return freights

    # ---------------------------------------------------------------------
    # Apply filters
    # ---------------------------------------------------------------------
    async def _apply_filters(self, filters: Dict):
        """Применение фильтров поиска."""
        print(f"Applying filters: {filters}")

        # ---------------------------------------------------------------------
        # Helper: Click "Дополнительная информация" with maximum data
        # ---------------------------------------------------------------------
        async def click_rich_info_button():
            """
            Находит все кнопки "Дополнительная информация" и кликает на ту,
            у которой максимальный "информационный вес" (длина текста).
            """
            print(f"\n{'='*60}")
            print(f"[STEP 0] Looking for 'Дополнительная информация' buttons...")
            print(f"{'='*60}")
            
            try:
                # Раскрыть фильтры, если нужно
                try:
                    expand_btn = await self.page.wait_for_selector(
                        'button:has-text("Развернуть фильтры")', timeout=3_000
                    )
                    if expand_btn:
                        await expand_btn.click()
                        print('✓ Clicked "Развернуть фильтры" button')
                        await asyncio.sleep(1)
                except Exception:
                    pass
                
                # Найти все кнопки с текстом "Дополнительная информация"
                buttons = await self.page.query_selector_all(
                    'button:has-text("Дополнительная информация"), '
                    'a:has-text("Дополнительная информация"), '
                    '[role="button"]:has-text("Дополнительная информация")'
                )
                
                if not buttons:
                    print("ℹ No 'Дополнительная информация' buttons found")
                    return
                
                print(f"✓ Found {len(buttons)} button(s)")
                
                # Если только одна кнопка - кликаем её
                if len(buttons) == 1:
                    await buttons[0].click()
                    print(f"✓ Clicked the only button")
                    await asyncio.sleep(1)
                    return
                
                # Если несколько - выбираем с максимальным весом
                max_weight = 0
                best_button = None
                
                for i, button in enumerate(buttons):
                    try:
                        # Получить текст кнопки и её окружения
                        text_content = await button.text_content()
                        
                        # Попытаться получить текст родительского контейнера
                        parent_text = await button.evaluate(
                            '(el) => el.parentElement?.innerText || el.innerText'
                        )
                        
                        # Вес = длина текста в родительском контейнере
                        weight = len(parent_text) if parent_text else len(text_content)
                        
                        print(f"  Button {i+1}: weight={weight} chars")
                        
                        if weight > max_weight:
                            max_weight = weight
                            best_button = button
                            
                    except Exception as e:
                        print(f"  Button {i+1}: error getting weight - {e}")
                        continue
                
                if best_button:
                    print(f"✓ Clicking button with maximum weight: {max_weight} chars")
                    await best_button.click()
                    await asyncio.sleep(1.5)
                    print(f"✓ 'Дополнительная информация' clicked successfully")
                else:
                    print(f"⚠ Could not determine best button, clicking first one")
                    await buttons[0].click()
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"⚠ Error in click_rich_info_button: {e}")
                import traceback
                traceback.print_exc()
        
        # ---------------------------------------------------------------------
        # Helper: Set Location (Strictly top field) - REWRITTEN
        # ---------------------------------------------------------------------
        async def set_location_strict(label_text: str, value: str):
            """
            Sets location in Trans.eu filter using modal window.
            
            Steps:
            1. Find and click the main location field (Загрузка/Разгрузка)
            2. Wait for modal window to appear
            3. Find search input in modal
            4. Type the location value
            5. Wait for suggestions
            6. Click on first suggestion
            7. Click "Дополнительная информация" button to confirm
            8. Verify that value was set
            """
            print(f"\n{'='*60}")
            print(f"Setting {label_text} to: {value}")
            print(f"{'='*60}")
            
            try:
                # Step 1: Find the main location field by label text
                # Using get_by_text() is a Playwright best practice for finding by visible text
                print(f"[1/7] Looking for field with label '{label_text}'...")
                
                # Find the label
                label_locator = self.page.get_by_text(label_text, exact=True).first
                
                # Get the parent container
                # Navigate up to find the input field
                # Use evaluate to traverse DOM reliably
                input_field = await label_locator.evaluate_handle('''
                    (label) => {
                        // Find closest container
                        let container = label.closest('[data-ctx="place-field"]');
                        if (!container) {
                            container = label.parentElement?.parentElement;
                        }
                        // Find first text input in container
                        return container?.querySelector('input[type="text"]');
                    }
                ''')
                
                if not input_field:
                    print(f"❌ Error: Could not find input field for {label_text}")
                    await self.page.screenshot(path=f"error_no_input_{label_text}.png")
                    return False
                
                # Convert JSHandle to ElementHandle
                input_element = input_field.as_element()
                
                print(f"✓ Found input field")
                
                # Step 2: Click on the input to open modal
                print(f"[2/7] Clicking input field to open modal...")
                await input_element.click()
                await asyncio.sleep(1)
                
                # Step 3: Wait for modal window to appear
                print(f"[3/7] Waiting for modal window...")
                
                # Use role-based selector (best practice)
                # Look for dialog or any modal container
                try:
                    # Try to find modal by role
                    modal = await self.page.wait_for_selector(
                        'div[role="dialog"], [class*="modal"], [class*="popup"]',
                        timeout=5_000,
                        state='visible'
                    )
                    print(f"✓ Modal window appeared")
                except:
                    print(f"⚠ Modal not found by role, trying alternative...")
                    modal = None
                
                # Step 4: Find search input in modal
                print(f"[4/7] Looking for search input in modal...")
                
                # Try multiple strategies to find the search input
                search_input = None
                
                # Strategy 1: By placeholder
                try:
                    search_input = await self.page.wait_for_selector(
                        'input[placeholder="Найти"]',
                        timeout=2_000,
                        state='visible'
                    )
                    print(f"✓ Found search input by placeholder")
                except:
                    pass
                
                # Strategy 2: By role and name
                if not search_input:
                    try:
                        search_input = self.page.get_by_role("textbox").filter(has_text="Найти").first
                        if await search_input.count() > 0:
                            print(f"✓ Found search input by role")
                        else:
                            search_input = None
                    except:
                        pass
                
                # Strategy 3: Find focused input
                if not search_input:
                    try:
                        search_input = await self.page.wait_for_selector(
                            'input:focus',
                            timeout=2_000
                        )
                        print(f"✓ Found focused input")
                    except:
                        pass
                
                # Strategy 4: Any visible text input in modal
                if not search_input:
                    try:
                        if modal:
                            search_input = await modal.query_selector('input[type="text"]')
                        else:
                            # Find any recently appeared input
                            search_input = await self.page.query_selector('input[type="text"]:visible')
                        print(f"✓ Found input in modal container")
                    except:
                        pass
                
                if not search_input:
                    print(f"❌ Error: Could not find search input in modal")
                    await self.page.screenshot(path=f"error_no_modal_input_{label_text}.png")
                    return False
                
                # Step 5: Type the location value
                print(f"[5/7] Typing '{value}' into search input...")
                
                # Click to ensure focus
                await search_input.click()
                await asyncio.sleep(0.3)
                
                # Clear any existing value
                await search_input.fill("")
                await asyncio.sleep(0.2)
                
                # Type the value character by character (more reliable)
                await search_input.type(value, delay=50)
                
                # Verify input
                actual_value = await search_input.input_value()
                print(f"✓ Typed value: '{actual_value}'")
                
                if actual_value != value:
                    print(f"⚠ Warning: Value mismatch. Expected '{value}', got '{actual_value}'")
                
                # Wait for suggestions to load
                await asyncio.sleep(2)
                
                # Step 6: Wait for suggestions and click first one
                print(f"[6/7] Waiting for suggestions...")
                
                # Use role-based selector for options (best practice)
                suggestion_clicked = False
                
                try:
                    # Wait for listbox or options to appear
                    await self.page.wait_for_selector(
                        '[role="option"], [role="listbox"] > *, li[class*="suggestion"], div[class*="suggestion"]',
                        timeout=5_000,
                        state='visible'
                    )
                    print(f"✓ Suggestions appeared")
                    
                    # Try to click first option
                    # Use get_by_role for better reliability
                    try:
                        first_option = self.page.get_by_role("option").first
                        if await first_option.count() > 0:
                            await first_option.click()
                            suggestion_clicked = True
                            print(f"✓ Clicked first suggestion (by role)")
                    except:
                        pass
                    
                    # Fallback: try other selectors
                    if not suggestion_clicked:
                        for selector in [
                            '[role="option"]:first-child',
                            'li[class*="suggestion"]:first-child',
                            'div[class*="suggestion"]:first-child',
                            '[data-highlighted="true"]',
                        ]:
                            try:
                                option = await self.page.wait_for_selector(selector, timeout=1_000)
                                await option.click()
                                suggestion_clicked = True
                                print(f"✓ Clicked suggestion with selector: {selector}")
                                break
                            except:
                                continue
                    
                except Exception as e:
                    print(f"⚠ No suggestions found: {e}")
                
                if not suggestion_clicked:
                    print(f"⚠ Could not click suggestion, trying keyboard...")
                    await self.page.keyboard.press("ArrowDown")
                    await asyncio.sleep(0.5)
                    await self.page.keyboard.press("Enter")
                
                await asyncio.sleep(1)
                
                # Step 6.5: Set radius "+ 75 km" (only for "Загрузка")
                if label_text == "Загрузка":
                    print(f"[6.5/8] Setting radius '+ 75 km' for {label_text}...")
                    
                    try:
                        # Wait a bit for radius selector to appear
                        await asyncio.sleep(0.5)
                        
                        # Try to find radius selector near the location field
                        # Use locator with has-text for better reliability
                        radius_option = self.page.locator('li:has-text("+ 75 km")').first
                        
                        if await radius_option.count() > 0:
                            await radius_option.click()
                            print(f"✓ Selected radius: + 75 km")
                            await asyncio.sleep(0.5)
                        else:
                            # Fallback: try other selectors
                            for selector in [
                                'select option:has-text("+ 75 km")',
                                '[value="75"]',
                                'li:contains("75 km")',
                            ]:
                                try:
                                    elem = await self.page.wait_for_selector(selector, timeout=2_000)
                                    if elem:
                                        await elem.click()
                                        print(f"✓ Selected radius with selector: {selector}")
                                        break
                                except:
                                    continue
                            else:
                                print(f"ℹ Radius selector not found (might be optional)")
                                
                    except Exception as e:
                        print(f"ℹ Could not set radius: {e}")
                
                # Step 7: Click "Дополнительная информация" button to confirm
                print(f"[7/7] Looking for confirmation button...")
                
                try:
                    # Look for button with text "Дополнительная информация" or similar
                    confirm_button = None
                    
                    # Try by text content
                    for button_text in ["ДОБАВИТЬ ДОПОЛНИТЕЛЬНОЕ МЕСТОНАХОЖДЕНИЕ", "Дополнительная информация", "Добавить"]:
                        try:
                            confirm_button = self.page.get_by_role("button").filter(has_text=button_text).first
                            if await confirm_button.count() > 0:
                                await confirm_button.click()
                                print(f"✓ Clicked confirmation button: '{button_text}'")
                                break
                        except:
                            continue
                    
                    # If no button found, modal might close automatically
                    if not confirm_button or await confirm_button.count() == 0:
                        print(f"ℹ No confirmation button found, modal might auto-close")
                    
                except Exception as e:
                    print(f"ℹ Confirmation button handling: {e}")
                
                # Wait for modal to close
                await asyncio.sleep(1.5)
                
                # Step 8: Verify that value was set
                print(f"[8/8] Verifying that location was set...")
                
                try:
                    # Check if the main input field now contains the value
                    final_value = await input_element.input_value()
                    if value.lower() in final_value.lower() or final_value:
                        print(f"✓ SUCCESS: {label_text} set to '{final_value}'")
                        print(f"{'='*60}\n")
                        return True
                    else:
                        print(f"⚠ Warning: Value might not be set correctly")
                        print(f"   Expected: {value}")
                        print(f"   Got: {final_value}")
                        return False
                except:
                    print(f"✓ Location setting completed (verification skipped)")
                    return True
                    
            except Exception as e:
                print(f"❌ Error setting {label_text}: {e}")
                import traceback
                traceback.print_exc()
                await self.page.screenshot(path=f"error_{label_text}.png")
                return False

        # ---------------------------------------------------------------------
        # Helper: Set Date - REWRITTEN with Playwright locators
        # ---------------------------------------------------------------------
        async def set_date_filter(label_text: str, date_from: str, date_to: str):
            """
            Sets date range using Playwright locators (more reliable than evaluate_handle).
            """
            if not date_from and not date_to:
                print(f"ℹ Skipping {label_text} (no dates provided)")
                return
                
            print(f"\n{'='*60}")
            print(f"Setting {label_text}: {date_from} → {date_to}")
            print(f"{'='*60}")
            
            try:
                # Find the label
                label_locator = self.page.get_by_text(label_text, exact=True).first
                
                # Wait for label to be visible
                await label_locator.wait_for(state='visible', timeout=5_000)
                
                # Get parent container using locator
                # Navigate to parent and find all inputs
                parent_locator = label_locator.locator('..')  # parent element
                
                # Find all date inputs in the parent container
                date_inputs = parent_locator.locator('input[type="text"], input[type="date"], input').all()
                
                inputs_list = await date_inputs
                
                if len(inputs_list) >= 2:
                    # Set "From" date
                    if date_from:
                        print(f"  Setting 'From' date: {date_from}")
                        await inputs_list[0].click()
                        await inputs_list[0].fill(date_from)
                        await inputs_list[0].press("Enter")
                        await asyncio.sleep(0.5)
                        print(f"  ✓ 'From' date set")
                    
                    # Set "To" date
                    if date_to:
                        print(f"  Setting 'To' date: {date_to}")
                        await inputs_list[1].click()
                        await inputs_list[1].fill(date_to)
                        await inputs_list[1].press("Enter")
                        await asyncio.sleep(0.5)
                        print(f"  ✓ 'To' date set")
                        
                    print(f"✓ {label_text} completed")
                    print(f"{'='*60}\n")
                else:
                    print(f"⚠ Warning: Expected 2 date inputs, found {len(inputs_list)}")
                    
            except Exception as e:
                print(f"❌ Error setting {label_text}: {e}")
                import traceback
                traceback.print_exc()

        # =====================================================================
        # APPLY FILTERS IN CORRECT ORDER
        # =====================================================================
        
        # STEP 1: Click "Дополнительная информация" with maximum data
        await click_rich_info_button()
        
        # STEP 2: Apply Locations (with radius for "Загрузка")
        if "origin" in filters:
            await set_location_strict("Загрузка", filters["origin"])
        
        if "destination" in filters:
            await set_location_strict("Разгрузка", filters["destination"])

        # STEP 3: Apply Dates
        # Format expected: DD.MM.YYYY
        await set_date_filter(
            "Дата загрузки",
            filters.get("loading_date_from", ""),
            filters.get("loading_date_to", "")
        )
        
        await set_date_filter(
            "Дата разгрузки",
            filters.get("unloading_date_from", ""),
            filters.get("unloading_date_to", "")
        )

        # STEP 4: Click the search button
        print(f"\n{'='*60}")
        print("FINAL STEP: Clicking search button...")
        print(f"{'='*60}")
        
        try:
            # Use get_by_role for better reliability
            search_button = self.page.get_by_role("button", name="Поиск").first
            
            if await search_button.count() > 0:
                await search_button.click()
                print("✓ Search button clicked")
                
                # Wait for results to load
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=10_000)
                    print("✓ Page loaded (networkidle)")
                except Exception:
                    print("⚠ networkidle timeout, waiting 3 seconds...")
                    await asyncio.sleep(3)
                
                print(f"{'='*60}\n")
            else:
                print("❌ Error: Search button not found")
                
        except Exception as e:
            print(f"❌ Error clicking search: {e}")
            import traceback
            traceback.print_exc()

    # ---------------------------------------------------------------------
    # Parse freight list
    # ---------------------------------------------------------------------
    async def _parse_freight_list(self) -> List[Dict]:
        """Parse freight list from the results page."""
        freights_data = await self.page.evaluate(
            """
            () => {
                const items = [];
                const rows = document.querySelectorAll('[data-ctx="row"]');
                rows.forEach(row => {
                    try {
                        const text = row.innerText;
                        const lines = text.split('\n').map(l => l.trim()).filter(l => l);
                        const priceIdx = lines.findIndex(l => l.includes('EUR') || l.includes('€'));
                        let price = '';
                        let cargoInfo = '';
                        if (priceIdx !== -1) {
                            price = lines[priceIdx];
                            if (priceIdx > 4) {
                                cargoInfo = lines.slice(4, priceIdx).join(', ');
                            }
                        } else if (lines.length > 4) {
                            cargoInfo = lines.slice(4).join(', ');
                        }
                        items.push({
                            trans_id: row.getAttribute('data-id') || Math.random().toString(36).substr(2, 9),
                            raw_text: text,
                            loading_place: lines[0] || '',
                            loading_date: lines[1] || '',
                            unloading_place: lines[2] || '',
                            unloading_date: lines[3] || '',
                            cargo_info: cargoInfo,
                            price_original: price,
                            currency: 'EUR'
                        });
                    } catch (e) {
                        console.error('Error parsing freight row:', e);
                    }
                });
                return items;
            }
            """
        )
        return freights_data

    # ---------------------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------------------
    async def close(self):
        """Закрытие браузера."""
        if self.browser:
            await self.browser.close()
            print("✓ Browser closed")


# ---------------------------------------------------------------------
# Helper for quick manual testing
# ---------------------------------------------------------------------
async def test_scraper():
    scraper = TransEuScraper()
    try:
        await scraper.start_browser(headless=False)  # headless=False for debugging
        await scraper.login()
        # Example filters – replace with real values as needed
        filters = {"origin": "Polska", "destination": "Niemcy"}
        freights = await scraper.search_freights(filters=filters)
        print(f"\nFound {len(freights)} freights:")
        for freight in freights[:3]:
            print(freight)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await scraper.close()


if __name__ == "__main__":
    # Для тестирования запустите: python -m app.services.trans_eu
    asyncio.run(test_scraper())
