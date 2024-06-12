from playwright.async_api import Page, ElementHandle
from typing import List
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Playwright,
    ElementHandle,
)


class WebBrowser:
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None

    async def launch(self, headless=False):
        self.playwright: Playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        print("Browser launched.")

    async def close(self):
        if self.browser:
            await self.browser.close()
            await self.playwright.stop()
            print("Browser closed.")

    async def _ensure_page_initialized(self):
        if not self.page:
            self.page = await self.browser.new_page()

    async def navigate_to(self, url: str, timeout: int = 30000):
        await self._ensure_page_initialized()
        try:
            await self.page.goto(url, timeout=timeout)
            print(f"Navigated to {url}")
        except PlaywrightTimeoutError:
            raise TimeoutError(f"Timed out waiting for navigation to '{url}'.")

    async def click_element(self, selector: str, timeout: int = 5000):
        await self._ensure_page_initialized()
        try:
            await self.page.click(selector, timeout=timeout)
            print(f"Clicked element: {selector}")
        except PlaywrightTimeoutError:
            raise TimeoutError(
                f"Timed out waiting for element '{selector}' to be clickable"
            )

    async def fill_input(self, selector: str, value: str, delay: int = 100):
        await self._ensure_page_initialized()
        try:
            await self.page.type(selector, value, delay=delay)
            print(f"Filled input: {selector} with value: {value}")
        except PlaywrightTimeoutError:
            raise TimeoutError(f"Timed out trying to fill input '{selector}'")

    async def get_text(self, selector: str) -> str:
        await self._ensure_page_initialized()
        try:
            text = await self.page.inner_text(selector)
            print(f"Got text for {selector}: {text}")
            return text
        except PlaywrightTimeoutError:
            raise TimeoutError(f"Timed out trying to get text from '{selector}'")

    async def take_screenshot(self, file_path: str):
        await self._ensure_page_initialized()
        await self.page.screenshot(path=file_path)
        print(f"Screenshot taken: {file_path}")

    async def find_elements(self, selector: str) -> List[ElementHandle]:
        await self._ensure_page_initialized()
        try:
            elements = await self.page.query_selector_all(selector)
            print(f"Found elements for selector: {selector}")
            return elements
        except PlaywrightTimeoutError:
            raise TimeoutError(f"Timed out trying to find elements '{selector}'")

    async def get_page_metadata(self) -> dict:
        await self._ensure_page_initialized()
        title = await self.page.title()
        description_meta = await self.page.query_selector("meta[name='description']")
        description_content = (
            (await description_meta.get_attribute("content"))
            if description_meta
            else ""
        )
        metadata = {
            "title": title,
            "meta_description": description_content,
        }
        print(f"Page metadata: {metadata}")
        return metadata

    async def get_elements_metadata(self, selectors: dict) -> dict:
        await self._ensure_page_initialized()
        metadata = {}
        for key, selector in selectors.items():
            elements = await self.find_elements(selector)
            metadata[key] = [
                {
                    "id": await el.get_attribute("id"),
                    "class": await el.get_attribute("class"),
                    "inner_text": await el.inner_text(),
                }
                for el in elements
            ]
        print(f"Elements metadata: {metadata}")
        return metadata

    ################################################################################
    # Network activity
    ################################################################################
    async def click_and_wait_for_network_activity(self, selector, timeout=5000):
        pending_requests = 0

        async def request_handler(route, request):
            nonlocal pending_requests
            pending_requests += 1
            print(f"Request: {request.method} {request.url}")
            await route.continue_()

        async def response_handler(response):
            nonlocal pending_requests
            print(f"Response: {response.status} {response.url}")
            if response.status == 200 and response.request.method != "OPTIONS":
                pending_requests -= 1
                print(f"Pending requests: {pending_requests}")
                if pending_requests == 0:
                    await self.page.evaluate("window.networkActivityComplete = true")

        await self.page.route("**/*", request_handler)
        self.page.on("response", response_handler)

        await self.page.evaluate("window.networkActivityComplete = false")
        await self.page.click(selector)

        try:
            await self.page.wait_for_function(
                "window.networkActivityComplete === true", timeout=timeout
            )
            return True
        except PlaywrightTimeoutError:
            print("Timeout occurred")
            return False
        finally:
            await self.page.unroute("**/*", request_handler)
            self.page.remove_listener("response", response_handler)

    async def wait_for_selector(self, selector: str, timeout: int = 5000):
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
        except PlaywrightTimeoutError:
            raise TimeoutError(f"Timed out waiting for selector '{selector}'")

    async def wait_for_navigation(self, page: Page = None, timeout: int = 30000):
        if page is None:
            page = self.page
        await page.wait_for_load_state("networkidle", timeout=timeout)


class NavigationError(Exception):
    pass


class ElementNotFoundError(Exception):
    pass


class InteractionError(Exception):
    pass
