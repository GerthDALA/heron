"""Async storefront crawler built on Crawl4AI (stealth mode).

Crawl4AI is imported lazily so the rest of the application (regex engine,
risk calculator, API) keeps working in environments where the headless
browser stack is unavailable — a failed page never crashes a scan.
"""

import asyncio
import logging
import random
import re
from urllib.parse import urljoin, urlparse

logger = logging.getLogger("heron.crawler")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

PRODUCT_URL_HINTS = ("/product", "/produit", "/soin", "/serum", "/creme", "/collection", "/shop")

_TAG_RE = re.compile(r"<[^>]+>")
_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_META_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]*content=["\']([^"\']*)["\']',
    re.IGNORECASE,
)


def normalise_domain(domain: str) -> str:
    domain = domain.strip()
    if not domain.startswith(("http://", "https://")):
        domain = "https://" + domain
    return domain.rstrip("/")


def _strip_html(html: str) -> str:
    text = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    text = _TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_page(url: str, html: str, markdown: str | None = None) -> dict:
    title_match = _TITLE_RE.search(html or "")
    meta_match = _META_DESC_RE.search(html or "")
    body = (markdown or _strip_html(html or "")).strip()
    return {
        "url": url,
        "title": title_match.group(1).strip() if title_match else "",
        "meta_description": meta_match.group(1).strip() if meta_match else "",
        "body_text": body,
    }


def _discover_product_urls(base_url: str, html: str, limit: int) -> list[str]:
    base_netloc = urlparse(base_url).netloc
    found: list[str] = []
    seen: set[str] = set()
    for href in _HREF_RE.findall(html or ""):
        absolute = urljoin(base_url + "/", href).split("#")[0].rstrip("/")
        parsed = urlparse(absolute)
        if parsed.netloc != base_netloc:
            continue
        if not any(hint in parsed.path.lower() for hint in PRODUCT_URL_HINTS):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        found.append(absolute)
        if len(found) >= limit:
            break
    return found


async def _fetch_page(crawler, url: str) -> dict | None:
    """Fetch one URL through Crawl4AI; return extracted page or None on failure."""
    try:
        result = await crawler.arun(url=url, bypass_cache=True)
        if not getattr(result, "success", False):
            logger.warning("Crawl failed for %s: %s", url, getattr(result, "error_message", "unknown"))
            return None
        html = getattr(result, "html", "") or ""
        markdown = getattr(result, "markdown", None)
        if markdown is not None and not isinstance(markdown, str):
            markdown = getattr(markdown, "raw_markdown", None) or str(markdown)
        return _extract_page(url, html, markdown)
    except Exception as exc:  # never crash the full scan on one page
        logger.warning("Error crawling %s: %s", url, exc)
        return None


async def crawl_domain(domain: str, max_pages: int) -> list[dict]:
    """Crawl a storefront: homepage first, then discovered product pages."""
    from crawl4ai import AsyncWebCrawler  # lazy: heavy browser dependency

    base_url = normalise_domain(domain)
    pages: list[dict] = []

    async with AsyncWebCrawler(headless=True, user_agent=random.choice(USER_AGENTS), verbose=False) as crawler:
        home = await _fetch_page(crawler, base_url)
        home_html = ""
        if home is not None:
            pages.append(home)
            try:
                result = await crawler.arun(url=base_url, bypass_cache=False)
                home_html = getattr(result, "html", "") or ""
            except Exception:
                home_html = ""

        product_urls = _discover_product_urls(base_url, home_html, max_pages - len(pages))
        for url in product_urls:
            if len(pages) >= max_pages:
                break
            await asyncio.sleep(random.uniform(1.0, 3.0))  # stealth: randomised delay
            page = await _fetch_page(crawler, url)
            if page is not None:
                pages.append(page)

    return pages


async def crawl_homepage(domain: str) -> dict:
    """Crawl only the root URL of the domain."""
    from crawl4ai import AsyncWebCrawler  # lazy: heavy browser dependency

    base_url = normalise_domain(domain)
    async with AsyncWebCrawler(headless=True, user_agent=random.choice(USER_AGENTS), verbose=False) as crawler:
        page = await _fetch_page(crawler, base_url)
    if page is None:
        return {"url": base_url, "title": "", "body_text": ""}
    return page
