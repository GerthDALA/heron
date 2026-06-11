"""Crawler tests. The live-URL test is marked slow and skipped by default
(run with: pytest -m slow tests/test_crawler.py)."""

import pytest

from app.engine.crawler import _discover_product_urls, _extract_page, normalise_domain


def test_normalise_domain_adds_https():
    assert normalise_domain("example.fr") == "https://example.fr"


def test_normalise_domain_strips_trailing_slash():
    assert normalise_domain("https://example.fr/") == "https://example.fr"


def test_extract_page_strips_html():
    html = """<html><head><title>Sérum Visage</title>
    <meta name="description" content="Un sérum doux"></head>
    <body><script>var x=1;</script><h1>Notre sérum</h1><p>Texte produit.</p></body></html>"""
    page = _extract_page("https://example.fr/serum", html)
    assert page["title"] == "Sérum Visage"
    assert page["meta_description"] == "Un sérum doux"
    assert "<" not in page["body_text"]
    assert "Notre sérum" in page["body_text"]
    assert "var x=1" not in page["body_text"]


def test_private_hosts_detected():
    from app.engine.crawler import is_private_host
    assert is_private_host("http://127.0.0.1:8080")
    assert is_private_host("http://192.168.1.10")
    assert is_private_host("http://10.0.0.5/admin")
    assert is_private_host("http://[::1]:9000")


def test_discover_product_urls_filters_and_limits():
    html = """
    <a href="/produit/serum-eclat">a</a>
    <a href="/collection/soins">b</a>
    <a href="/about">c</a>
    <a href="https://other-domain.com/product/x">d</a>
    <a href="/produit/serum-eclat">dup</a>
    <a href="/shop/creme-nuit">e</a>
    """
    urls = _discover_product_urls("https://example.fr", html, limit=2)
    assert len(urls) == 2
    assert all(u.startswith("https://example.fr") for u in urls)
    assert "https://other-domain.com/product/x" not in urls


@pytest.mark.slow
@pytest.mark.asyncio
async def test_crawl_homepage_real_url():
    """Integration: requires network + headless browser stack."""
    from app.engine.crawler import crawl_homepage
    page = await crawl_homepage("https://www.typology.com")
    assert page["url"].startswith("https://")
    assert isinstance(page["body_text"], str)
