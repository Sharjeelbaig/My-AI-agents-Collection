"""Playwright wrapper. Lazy-loaded so the package can be imported without
Playwright installed (useful for unit tests that don't touch the browser).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional


@contextmanager
def browser_page(headless: bool = True, storage_state: Optional[str] = None) -> Iterator:
    """Yield a Playwright Page. The browser is closed when the context exits."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(storage_state=storage_state) if storage_state \
            else browser.new_context()
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()


__all__ = ["browser_page"]
