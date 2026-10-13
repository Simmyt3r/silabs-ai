import json

from scripts.audit_knowledge import audit_knowledge


def _write(path, rows):
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_audit_reports_coverage_and_manifest_match(tmp_path):
    corpus = tmp_path / "knowledge.jsonl"
    manifest = tmp_path / "manifest.json"
    _write(
        corpus,
        [
            {
                "text": "Official Supabase documentation content.",
                "source": "https://supabase.com/docs#chunk-1",
                "verified": True,
                "source_kind": "web_collection",
                "domain": "supabase.com",
                "trust_tier": "A",
                "authority": "official-docs",
                "retrieved_at": "2026-10-13T00:00:00+00:00",
                "content_hash": "one",
            },
            {
                "text": "First party product documentation.",
                "source": "https://github.com/Simmyt3r/app/blob/main/README.md#chunk-1",
                "verified": True,
                "source_kind": "github_repo",
                "domain": "silabs",
                "trust_tier": "A",
                "authority": "first-party",
                "retrieved_at": "2026-10-13T00:00:00+00:00",
                "content_hash": "two",
            },
        ],
    )
    manifest.write_text(
        json.dumps({"stats": {"chunks_written": 2}}),
        encoding="utf-8",
    )

    report = audit_knowledge(corpus, manifest)

    assert report["passed"] is True
    assert report["records"] == 2
    assert report["source_kinds"]["web_collection"] == 1
    assert report["source_kinds"]["github_repo"] == 1
    assert report["trust_tiers"]["A"] == 2
    assert report["warnings"] == []


def test_audit_warns_about_duplicate_hash_and_missing_metadata(tmp_path):
    corpus = tmp_path / "knowledge.jsonl"
    _write(
        corpus,
        [
            {
                "text": "One.",
                "source": "one",
                "verified": True,
                "content_hash": "same",
            },
            {
                "text": "Two.",
                "source": "two",
                "verified": False,
                "content_hash": "same",
            },
        ],
    )

    report = audit_knowledge(corpus)

    assert report["passed"] is True
    assert report["duplicate_hashes"] == 1
    assert report["unverified"] == 1
    assert report["missing_metadata"]["source_kind"] == 2
    assert any("duplicate content hashes" in item for item in report["warnings"])
    assert any("unverified records present" in item for item in report["warnings"])


def test_audit_rejects_invalid_json(tmp_path):
    corpus = tmp_path / "knowledge.jsonl"
    corpus.write_text("not-json\n", encoding="utf-8")

    report = audit_knowledge(corpus)

    assert report["passed"] is False
    assert report["errors"]
