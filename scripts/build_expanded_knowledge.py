from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

TEXT_EXTENSIONS = {".md", ".mdx", ".markdown", ".txt", ".rst", ".xml", ".html"}
DOC_WORDS = ("readme", "spec", "requirement", "roadmap", "architecture", "api", "decision", "policy", "guide")
MAX_BYTES = 1_500_000
USER_AGENT = "SilabsAI-KnowledgeBuilder/1.0"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def digest(text: str) -> str:
    value = " ".join(text.lower().split())
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def clean_repo_document(text: str, suffix: str) -> str:
    if suffix.lower() in {".xml", ".html"}:
        soup = BeautifulSoup(text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return normalize(soup.get_text("\n", strip=True))
    return clean_markdown(text)


def clean_markdown(text: str) -> str:
    text = re.sub(r"(?s)<!--.*?-->", " ", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"(?m)^#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*[-*+]\s+", "• ", text)
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    return normalize(text)


def pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    pages: list[str] = []
    for page in reader.pages:
        value = page.extract_text() or ""
        value = normalize(value)
        if value:
            pages.append(value)
    return normalize("\n\n".join(pages))


def html_text(html: str) -> tuple[str, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    for tag in soup(["script", "style", "noscript", "svg", "canvas", "form"]):
        tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    for tag in root.find_all(["nav", "footer", "header", "aside"]):
        tag.decompose()
    return normalize(root.get_text("\n", strip=True)), title


def chunks(text: str, target: int, overlap: int, minimum: int) -> list[str]:
    text = normalize(text)
    if len(text) < minimum:
        return []
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out: list[str] = []
    current = ""
    for part in parts:
        pieces = re.split(r"(?<=[.!?])\s+", part) if len(part) > target * 2 else [part]
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            candidate = (current + "\n\n" + piece).strip() if current else piece
            if len(candidate) <= target:
                current = candidate
                continue
            if current:
                if len(current) >= minimum:
                    out.append(current)
                tail = current[-overlap:].strip() if overlap else ""
                current = (tail + "\n\n" + piece).strip() if tail else piece
            else:
                start = 0
                while start < len(piece):
                    end = min(start + target, len(piece))
                    block = piece[start:end].strip()
                    if len(block) >= minimum:
                        out.append(block)
                    if end == len(piece):
                        break
                    start = max(end - overlap, start + 1)
    if len(current) >= minimum:
        out.append(current)
    return out


def allowed_doc(
    path: Path,
    excluded: set[str],
    include_roots: list[str] | None = None,
) -> bool:
    if any(part in excluded for part in path.parts):
        return False
    if include_roots:
        path_text = path.as_posix()
        if not any(
            path_text == root.rstrip("/")
            or path_text.startswith(root.rstrip("/") + "/")
            for root in include_roots
        ):
            return False
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return False
    if include_roots:
        return True
    low = path.name.lower()
    return "docs" in {p.lower() for p in path.parts} or any(word in low for word in DOC_WORDS)


def clone_repo(
    name: str,
    branch: str,
    target: Path,
    sparse_paths: list[str] | None = None,
) -> None:
    env = os.environ.copy()
    token = env.get("GITHUB_TOKEN")
    if token:
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
        env["GIT_CONFIG_VALUE_0"] = "Authorization: Bearer " + token
    cmd = [
        "git", "clone", "--depth=1", "--filter=blob:none",
        "--single-branch", "--branch", branch,
    ]
    if sparse_paths:
        cmd.append("--sparse")
    cmd.extend(["https://github.com/" + name + ".git", str(target)])

    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    if sparse_paths:
        subprocess.run(
            ["git", "sparse-checkout", "set", *sparse_paths],
            cwd=target,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )


def fetch_page(session: requests.Session, url: str) -> tuple[str, str | None]:
    response = session.get(url, timeout=45)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "application/pdf" in content_type or url.lower().split("?")[0].endswith(".pdf"):
        return pdf_text(response.content), None
    return html_text(response.text)


def sitemap_urls(
    session: requests.Session,
    sitemap_url: str,
    allow_prefixes: list[str],
    limit: int,
) -> list[str]:
    found: list[str] = []
    seen_sitemaps: set[str] = set()

    def visit(url: str, depth: int = 0) -> None:
        if len(found) >= limit or url in seen_sitemaps or depth > 3:
            return
        seen_sitemaps.add(url)
        response = session.get(url, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        locations = [
            (element.text or "").strip()
            for element in root.iter()
            if element.tag.endswith("loc") and (element.text or "").strip()
        ]

        if root.tag.endswith("sitemapindex"):
            for child in locations:
                visit(child, depth + 1)
                if len(found) >= limit:
                    break
            return

        for page_url in locations:
            if allow_prefixes and not any(page_url.startswith(prefix) for prefix in allow_prefixes):
                continue
            if page_url not in found:
                found.append(page_url)
            if len(found) >= limit:
                break

    visit(sitemap_url)
    return found


def build(
    registry_path: Path,
    seed_path: Path,
    output_path: Path,
    manifest_path: Path,
    max_repos: int | None = None,
    max_web: int | None = None,
    skip_collections: bool = False,
    max_collection_pages: int | None = None,
    resume: bool = False,
) -> dict:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    policy = registry["policy"]
    target = int(policy["chunking"]["target_chars"])
    overlap = int(policy["chunking"]["overlap_chars"])
    minimum = int(policy["chunking"]["min_chars"])
    excluded = set(policy.get("github_exclude_dirs", []))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    rows: list[dict] = []
    pending_lines: list[str] = []
    stats = {
        "seed_records": 0,
        "github_documents": 0,
        "web_documents": 0,
        "collection_documents": 0,
        "chunks_written": 0,
        "duplicates_skipped": 0,
        "private_repos_skipped": 0,
        "source_failures": 0,
        "resumed_records": 0,
    }

    if resume and output_path.exists():
        for raw in output_path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                continue
            text = normalize(str(row.get("text", "")))
            if not text:
                continue
            key = str(row.get("content_hash") or digest(text))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
        stats["resumed_records"] = len(rows)
        print("RESUME existing records:", len(rows))
    else:
        output_path.write_text("", encoding="utf-8")

    def flush_pending() -> None:
        if not pending_lines:
            return
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write("".join(pending_lines))
            handle.flush()
        pending_lines.clear()

    def add(row: dict) -> None:
        text = normalize(str(row.get("text", "")))
        if not text:
            return
        key = digest(text)
        if key in seen:
            stats["duplicates_skipped"] += 1
            return
        seen.add(key)
        row = dict(row)
        row["text"] = text
        row["content_hash"] = key
        rows.append(row)
        pending_lines.append(json.dumps(row, ensure_ascii=False) + "\n")
        if len(pending_lines) >= 50:
            flush_pending()

    if seed_path.exists():
        for line in seed_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            row.setdefault("source_kind", "seed")
            row.setdefault("trust_tier", "A")
            row.setdefault("authority", "approved-seed")
            row.setdefault("retrieved_at", now())
            add(row)
            stats["seed_records"] += 1

    repo_sources = registry.get("github_repositories", [])
    if max_repos is not None:
        repo_sources = repo_sources[:max_repos]

    for source in repo_sources:
        name = source["repository"]
        branch = source.get("default_branch", "main")
        include_roots = list(source.get("include_roots", []))
        if source.get("requires_token") and not os.environ.get("GITHUB_TOKEN"):
            stats["private_repos_skipped"] += 1
            print("SKIP private repo (set GITHUB_TOKEN to include):", name)
            continue
        with tempfile.TemporaryDirectory(prefix="silabs-kb-") as tmp:
            root = Path(tmp) / "repo"
            try:
                clone_repo(name, branch, root, include_roots or None)
            except Exception as exc:
                stats["source_failures"] += 1
                print("WARN github", name, str(exc))
                continue
            for path in sorted(root.rglob("*")):
                if not path.is_file():
                    continue
                rel = path.relative_to(root)
                if not allowed_doc(rel, excluded, include_roots) or path.stat().st_size > MAX_BYTES:
                    continue
                raw = path.read_text(encoding="utf-8", errors="ignore")
                pieces = chunks(
                    clean_repo_document(raw, path.suffix),
                    target,
                    overlap,
                    minimum,
                )
                if not pieces:
                    continue
                stats["github_documents"] += 1
                base = "https://github.com/" + name + "/blob/" + branch + "/" + rel.as_posix()
                for idx, piece in enumerate(pieces, 1):
                    add({
                        "title": name + ": " + rel.name,
                        "text": piece,
                        "source": base + "#chunk-" + str(idx),
                        "verified": bool(source.get("verified")),
                        "trust_tier": source.get("trust_tier"),
                        "authority": source.get("authority"),
                        "domain": source.get("domain"),
                        "source_scope": source.get("source_scope", "first-party"),
                        "source_kind": "github_repo",
                        "repository": name,
                        "path": rel.as_posix(),
                        "chunk_index": idx,
                        "retrieved_at": now(),
                    })

    web_sources = registry.get("web_pages", [])
    if max_web is not None:
        web_sources = web_sources[:max_web]
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    for source in web_sources:
        url = source["url"]
        try:
            text, page_title = fetch_page(session, url)
        except Exception as exc:
            stats["source_failures"] += 1
            print("WARN web", url, str(exc))
            continue
        pieces = chunks(text, target, overlap, minimum)
        if not pieces:
            continue
        stats["web_documents"] += 1
        title = source.get("title") or page_title or url
        for idx, piece in enumerate(pieces, 1):
            add({
                "title": title,
                "text": piece,
                "source": url + "#chunk-" + str(idx),
                "verified": bool(source.get("verified")),
                "trust_tier": source.get("trust_tier"),
                "authority": source.get("authority"),
                "domain": source.get("domain"),
                "source_kind": "web_page",
                "chunk_index": idx,
                "retrieved_at": now(),
            })

    if not skip_collections:
        for source in registry.get("web_collections", []):
            page_limit = int(source.get("max_pages", 100))
            if max_collection_pages is not None:
                page_limit = min(page_limit, max_collection_pages)
            try:
                urls = sitemap_urls(
                    session,
                    source["sitemap_url"],
                    list(source.get("allow_prefixes", [])),
                    page_limit,
                )
            except Exception as exc:
                stats["source_failures"] += 1
                print("WARN sitemap", source.get("name"), str(exc))
                continue

            print("COLLECTION", source.get("name"), "pages:", len(urls))
            for page_number, url in enumerate(urls, 1):
                try:
                    text, page_title = fetch_page(session, url)
                except Exception as exc:
                    stats["source_failures"] += 1
                    print("WARN collection page", url, str(exc))
                    continue
                pieces = chunks(text, target, overlap, minimum)
                if not pieces:
                    continue
                stats["collection_documents"] += 1
                title = page_title or source.get("name") or url
                for idx, piece in enumerate(pieces, 1):
                    add({
                        "title": title,
                        "text": piece,
                        "source": url + "#chunk-" + str(idx),
                        "verified": bool(source.get("verified")),
                        "trust_tier": source.get("trust_tier"),
                        "authority": source.get("authority"),
                        "domain": source.get("domain"),
                        "source_kind": "web_collection",
                        "collection": source.get("name"),
                        "chunk_index": idx,
                        "retrieved_at": now(),
                    })
                if page_number < len(urls):
                    time.sleep(float(source.get("delay_seconds", 0.05)))

    flush_pending()
    stats["chunks_written"] = len(rows)
    manifest = {
        "schema_version": 1,
        "built_at": now(),
        "registry": str(registry_path),
        "seed": str(seed_path),
        "output": str(output_path),
        "stats": stats,
        "registered": {
            "github": len(registry.get("github_repositories", [])),
            "web": len(registry.get("web_pages", [])),
            "collections": len(registry.get("web_collections", [])),
        },
        "chunking": {"target_chars": target, "overlap_chars": overlap, "min_chars": minimum},
        "resume_enabled": resume,
        "complete": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("knowledge/source_registry.json"))
    parser.add_argument("--seed", type=Path, default=Path("knowledge/verified.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("knowledge/generated/verified.jsonl"))
    parser.add_argument("--manifest", type=Path, default=Path("knowledge/generated/manifest.json"))
    parser.add_argument("--max-repos", type=int)
    parser.add_argument("--max-web-pages", type=int)
    parser.add_argument("--skip-collections", action="store_true")
    parser.add_argument("--max-collection-pages", type=int)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue from an existing output JSONL and deduplicate new chunks.",
    )
    args = parser.parse_args()

    stats = build(
        args.registry, args.seed, args.output, args.manifest,
        max_repos=args.max_repos,
        max_web=args.max_web_pages,
        skip_collections=args.skip_collections,
        max_collection_pages=args.max_collection_pages,
        resume=args.resume,
    )
    print("\nSILABS KNOWLEDGE EXPANSION COMPLETE")
    for key, value in stats.items():
        print(key.replace("_", " ") + ":", value)


if __name__ == "__main__":
    main()
