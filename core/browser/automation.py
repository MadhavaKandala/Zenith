"""
Zenith Browser Automation — Playwright-based web automation.

Provides programmatic browser control for web scraping, form filling,
and UI testing. Falls back gracefully when Playwright is not installed.

Usage:
    from core.browser.automation import BrowserAutomation
    async with BrowserAutomation() as browser:
        page = await browser.new_page("https://example.com")
        content = await browser.get_text(page)
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("zenith.browser.automation")

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext

    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False
    logger.warning(
        "Playwright not installed. Browser automation will be unavailable. "
        "Install with: pip install playwright && playwright install chromium"
    )


class BrowserAutomation:
    """Playwright-based browser automation for Zenith."""

    def __init__(self, headless: bool = True):
        """
        Initialize browser automation.

        Args:
            headless: Run browser in headless mode (default True).
        """
        self.available = _PLAYWRIGHT_AVAILABLE
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.stop()

    async def start(self) -> None:
        """Launch the browser instance."""
        if not self.available:
            raise RuntimeError("Playwright is not available. Install with: pip install playwright")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context(
            user_agent="Zenith-AI/1.0 (Desktop Assistant)"
        )
        logger.info("Browser automation started (headless=%s)", self.headless)

    async def stop(self) -> None:
        """Close the browser and cleanup."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser automation stopped")

    async def new_page(self, url: Optional[str] = None) -> Page:
        """
        Open a new browser page.

        Args:
            url: Optional URL to navigate to immediately.

        Returns:
            Playwright Page object.
        """
        if not self._context:
            raise RuntimeError("Browser not started. Call start() first.")

        page = await self._context.new_page()
        if url:
            await page.goto(url, wait_until="domcontentloaded")
            logger.info("Navigated to: %s", url)
        return page

    async def get_text(self, page: Page) -> str:
        """
        Extract all visible text from a page.

        Args:
            page: Playwright Page object.

        Returns:
            Page text content.
        """
        return await page.inner_text("body")

    async def get_html(self, page: Page) -> str:
        """Get the full HTML content of a page."""
        return await page.content()

    async def screenshot(self, page: Page, path: str) -> str:
        """
        Take a screenshot of the page.

        Args:
            page: Playwright Page object.
            path: Output file path.

        Returns:
            Path to the saved screenshot.
        """
        await page.screenshot(path=path, full_page=True)
        logger.info("Screenshot saved: %s", path)
        return path

    async def click_element(self, page: Page, selector: str) -> None:
        """Click an element on the page by CSS selector."""
        await page.click(selector)
        logger.info("Clicked element: %s", selector)

    async def fill_input(self, page: Page, selector: str, value: str) -> None:
        """Fill an input field on the page."""
        await page.fill(selector, value)
        logger.info("Filled input %s", selector)

    async def evaluate_js(self, page: Page, expression: str) -> any:
        """Execute JavaScript on the page and return the result."""
        return await page.evaluate(expression)

    async def wait_for_selector(self, page: Page, selector: str, timeout: int = 5000) -> None:
        """Wait for an element to appear on the page."""
        await page.wait_for_selector(selector, timeout=timeout)

    async def scrape_page(self, url: str) -> dict:
        """
        Scrape a webpage and return structured content.

        Args:
            url: URL to scrape.

        Returns:
            Dict with 'title', 'text', 'links', and 'url'.
        """
        page = await self.new_page(url)
        try:
            title = await page.title()
            text = await self.get_text(page)
            links = await page.eval_on_selector_all(
                "a[href]",
                "elements => elements.map(e => ({text: e.innerText.trim(), href: e.href})).filter(l => l.text)"
            )
            return {
                "url": url,
                "title": title,
                "text": text[:5000],
                "links": links[:50],
            }
        finally:
            await page.close()

    async def search_google(self, query: str) -> list[dict]:
        """
        Perform a Google search and return results.

        Args:
            query: Search query string.

        Returns:
            List of dicts with 'title', 'url', 'snippet'.
        """
        page = await self.new_page(f"https://www.google.com/search?q={query}")
        try:
            await page.wait_for_selector("div#search", timeout=5000)
            results = await page.eval_on_selector_all(
                "div.g",
                """elements => elements.map(e => {
                    const title = e.querySelector('h3')?.innerText || '';
                    const link = e.querySelector('a')?.href || '';
                    const snippet = e.querySelector('.VwiC3b')?.innerText || '';
                    return { title, url: link, snippet };
                }).filter(r => r.title && r.url)"""
            )
            return results[:10]
        except Exception as exc:
            logger.error("Google search failed: %s", exc)
            return []
        finally:
            await page.close()
