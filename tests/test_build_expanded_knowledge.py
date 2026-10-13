import json

from scripts.build_expanded_knowledge import (
    chunks,
    clean_markdown,
    digest,
    html_text,
    sitemap_urls,
)


def test_chunk_text_splits_large_text_without_empty_chunks():
    text = ("Alpha sentence. Beta sentence. Gamma sentence. " * 80).strip()

    parts = chunks(
        text,
        target=220,
        overlap=30,
        minimum=40,
    )

    assert len(parts) > 2
    assert all(len(part) >= 40 for part in parts)


def test_clean_markdown_removes_common_markup():
    raw = "# Title\n\n- Item one\n- Item two\n\n[Docs](https://example.com)"
    cleaned = clean_markdown(raw)

    assert "# Title" not in cleaned
    assert "Title" in cleaned
    assert "Item one" in cleaned
    assert "Docs" in cleaned
    assert "https://example.com" not in cleaned


def test_html_to_text_prefers_main_content():
    html = """
    <html>
      <head><title>Example</title><style>.x{}</style></head>
      <body>
        <nav>Navigation noise</nav>
        <main><h1>Verified Page</h1><p>Useful factual content.</p></main>
        <footer>Footer noise</footer>
      </body>
    </html>
    """

    text, title = html_text(html)

    assert title == "Example"
    assert "Verified Page" in text
    assert "Useful factual content" in text
    assert "Navigation noise" not in text
    assert "Footer noise" not in text


def test_content_hash_is_whitespace_and_case_stable():
    assert digest("Silabs AI") == digest("  silabs   ai  ")



def test_sitemap_urls_filters_prefix_and_limit():
    class Response:
        content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://example.com/docs/a</loc></url>
          <url><loc>https://example.com/blog/b</loc></url>
          <url><loc>https://example.com/docs/c</loc></url>
        </urlset>"""
        def raise_for_status(self):
            return None

    class Session:
        def get(self, url, timeout=30):
            return Response()

    urls = sitemap_urls(
        Session(),
        "https://example.com/sitemap.xml",
        ["https://example.com/docs/"],
        1,
    )

    assert urls == ["https://example.com/docs/a"]
