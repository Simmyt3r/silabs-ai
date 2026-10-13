import json

from scripts.build_expanded_knowledge import (
    chunks,
    clean_markdown,
    digest,
    html_text,
    sitemap_urls,
    build,
    allowed_doc,
    clean_repo_document,
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



def test_build_resume_does_not_duplicate_existing_records(tmp_path):
    registry = tmp_path / "registry.json"
    seed = tmp_path / "seed.jsonl"
    output = tmp_path / "verified.jsonl"
    manifest = tmp_path / "manifest.json"

    registry.write_text(
        json.dumps(
            {
                "policy": {
                    "chunking": {
                        "target_chars": 300,
                        "overlap_chars": 30,
                        "min_chars": 20,
                    },
                    "github_exclude_dirs": [],
                },
                "github_repositories": [],
                "web_pages": [],
                "web_collections": [],
            }
        ),
        encoding="utf-8",
    )
    seed.write_text(
        json.dumps(
            {
                "title": "Seed",
                "text": "This is a stable verified seed record for resume testing.",
                "source": "silabs://seed/test",
                "verified": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    build(registry, seed, output, manifest)
    first = output.read_text(encoding="utf-8").splitlines()
    assert len(first) == 1

    stats = build(
        registry,
        seed,
        output,
        manifest,
        resume=True,
    )
    second = output.read_text(encoding="utf-8").splitlines()

    assert len(second) == 1
    assert stats["resumed_records"] == 1



def test_allowed_doc_accepts_sparse_root_even_without_docs_name():
    from pathlib import Path

    assert allowed_doc(
        Path("content/actions/quickstart.md"),
        excluded=set(),
        include_roots=["content/actions"],
    )


def test_clean_repo_document_extracts_xml_text():
    xml = """
    <chapter>
      <title>PostGIS Introduction</title>
      <para>PostGIS adds spatial capabilities to PostgreSQL.</para>
    </chapter>
    """

    cleaned = clean_repo_document(xml, ".xml")

    assert "PostGIS Introduction" in cleaned
    assert "spatial capabilities" in cleaned
    assert "<chapter>" not in cleaned


def test_build_resume_rewrites_duplicate_physical_records(tmp_path):
    registry = tmp_path / "registry.json"
    seed = tmp_path / "seed.jsonl"
    output = tmp_path / "verified.jsonl"
    manifest = tmp_path / "manifest.json"

    registry.write_text(
        json.dumps(
            {
                "policy": {
                    "chunking": {
                        "target_chars": 300,
                        "overlap_chars": 30,
                        "min_chars": 20,
                    },
                    "github_exclude_dirs": [],
                },
                "github_repositories": [],
                "web_pages": [],
                "web_collections": [],
            }
        ),
        encoding="utf-8",
    )
    seed.write_text("", encoding="utf-8")

    row = {
        "title": "Duplicate",
        "text": "This record was accidentally written twice during an earlier run.",
        "source": "silabs://resume/duplicate",
        "verified": True,
    }
    row["content_hash"] = digest(row["text"])
    duplicated = json.dumps(row) + "\n" + json.dumps(row) + "\n"
    output.write_text(duplicated, encoding="utf-8")

    stats = build(
        registry,
        seed,
        output,
        manifest,
        resume=True,
    )

    lines = [line for line in output.read_text(encoding="utf-8").splitlines() if line]
    assert len(lines) == 1
    assert stats["resumed_records"] == 1

    saved_manifest = json.loads(manifest.read_text(encoding="utf-8"))
    assert saved_manifest["stats"]["chunks_written"] == 1
