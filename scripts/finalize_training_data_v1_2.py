#!/usr/bin/env python3
"""Silabs AI finalizer v1.2: globally group normalized inputs before train/dev split."""

import argparse
import hashlib
import json
import random
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


CAPS = {
    "oasst1": 30000,
    "gsm8k": 7473,
    "arc_easy": 2251,
    "arc_challenge": 1119,
    "sciq": 11679,
    "openbookqa": 4957,
    "hotpotqa": 25000,
    "openmathinstruct2": 40000,
}


def clean(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return re.sub(r"\s+", " ", str(value)).strip()


def norm(value):
    return clean(value).lower()


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_jsonl(path: Path):
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except Exception as exc:
                print(f"WARN {path.name}:{line_number}: {exc}")
                continue
            if isinstance(item, dict):
                rows.append(item)
    return rows


def write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def role(node):
    if not isinstance(node, dict):
        return ""
    return clean(
        node.get("role") or node.get("speaker") or node.get("author")
    ).lower()


def text(node):
    if not isinstance(node, dict):
        return ""
    for key in ("text", "content", "message", "prompt"):
        if isinstance(node.get(key), str) and clean(node[key]):
            return clean(node[key])
    return ""


def children(node):
    if not isinstance(node, dict):
        return []
    for key in ("replies", "children"):
        if isinstance(node.get(key), list):
            return node[key]
    return []


def tree_pairs(tree):
    pairs = []

    def walk(node, last_user=""):
        if isinstance(node, list):
            for child in node:
                walk(child, last_user)
            return
        if not isinstance(node, dict):
            return

        current_role = role(node)
        current_text = text(node)
        next_user = last_user

        if current_role in ("user", "prompter", "human") and current_text:
            next_user = current_text
        elif (
            current_role in ("assistant", "bot", "gpt")
            and current_text
            and last_user
            and norm(current_text) != norm(last_user)
        ):
            pairs.append((last_user, current_text))

        for child in children(node):
            walk(child, next_user)

        for key in ("root", "tree", "messages"):
            if isinstance(node.get(key), (dict, list)):
                walk(node[key], next_user)

    walk(tree)
    return pairs


def flatten_oasst(rows):
    output = []
    self_copy = 0

    for row in rows:
        metadata = row.get("metadata") or {}
        pairs = (
            tree_pairs(metadata.get("raw_prompt_tree"))
            if metadata.get("raw_prompt_tree")
            else []
        )

        for user_text, assistant_text in pairs:
            if (
                not user_text
                or not assistant_text
                or norm(user_text) == norm(assistant_text)
            ):
                self_copy += 1
                continue

            record = {
                "id": "",
                "dataset": "oasst1",
                "task": "instruction_chat",
                "domain": "",
                "instruction": "Respond helpfully and accurately to the user.",
                "input": user_text,
                "output": assistant_text,
                "metadata": {
                    "source": metadata.get("source", "oasst1"),
                    "quality": "public_unreviewed",
                    "language": metadata.get("language", "mixed"),
                    "split": "train",
                    "message_tree_id": metadata.get("message_tree_id", ""),
                },
            }
            record["id"] = "oasst1_" + digest(
                norm(user_text) + "||" + norm(assistant_text)
            )[:16]
            output.append(record)

    return output, self_copy


def quality(record):
    input_text = clean(record.get("input"))
    output_text = clean(record.get("output"))
    return (
        len(input_text) >= 8
        and len(output_text) >= 1
        and len(input_text) <= 50000
        and len(output_text) <= 50000
        and norm(input_text) != norm(output_text)
    )


def dedup_input(rows):
    seen = set()
    output = []
    removed = 0

    for row in rows:
        key = digest(norm(row.get("input")))
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        output.append(row)

    return output, removed


def cap(rows, count, seed, name):
    if len(rows) <= count:
        return rows

    rng = random.Random(f"{seed}:{name}")
    indices = list(range(len(rows)))
    rng.shuffle(indices)
    return [rows[index] for index in sorted(indices[:count])]


def global_grouped_split(rows, ratio, seed):
    groups = defaultdict(list)
    for row in rows:
        groups[digest(norm(row.get("input")))].append(row)

    grouped_rows = list(groups.values())
    random.Random(f"{seed}:global-groups").shuffle(grouped_rows)

    target = round(len(rows) * ratio)
    train = []
    dev = []
    dev_count = 0

    for group in grouped_rows:
        if dev_count < target and len(grouped_rows) > 1:
            dev.extend(group)
            dev_count += len(group)
        else:
            train.extend(group)

    if not train and dev:
        train.extend(dev.pop())

    random.Random(f"{seed}:train").shuffle(train)
    random.Random(f"{seed}:dev").shuffle(dev)

    train_inputs = {digest(norm(row.get("input"))) for row in train}
    dev_inputs = {digest(norm(row.get("input"))) for row in dev}
    overlap = train_inputs & dev_inputs
    if overlap:
        raise RuntimeError(
            f"FATAL: {len(overlap)} normalized inputs cross train/dev"
        )

    stats = {
        "_global": {
            "records": len(rows),
            "input_groups": len(groups),
            "train": len(train),
            "dev": len(dev),
            "same_input_overlap": 0,
        }
    }

    for dataset in sorted({row.get("dataset", "") for row in rows}):
        train_count = sum(row.get("dataset") == dataset for row in train)
        dev_count_for_dataset = sum(row.get("dataset") == dataset for row in dev)
        stats[dataset] = {
            "total": train_count + dev_count_for_dataset,
            "train": train_count,
            "dev": dev_count_for_dataset,
        }

    return train, dev, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dev-ratio", type=float, default=0.02)
    parser.add_argument("--openmath-cap", type=int, default=40000)
    parser.add_argument("--hotpot-cap", type=int, default=25000)
    parser.add_argument("--oasst-cap", type=int, default=30000)
    args = parser.parse_args()

    if not 0 <= args.dev_ratio < 0.5:
        raise SystemExit("--dev-ratio must be >=0 and <0.5")

    root = Path(args.root).resolve()
    processed = root / "datasets" / "processed"
    final = processed / "final_v0_1"
    reports = root / "reports"
    final.mkdir(parents=True, exist_ok=True)
    reports.mkdir(exist_ok=True)

    caps = dict(CAPS)
    caps.update(
        oasst1=args.oasst_cap,
        hotpotqa=args.hotpot_cap,
        openmathinstruct2=args.openmath_cap,
    )

    print("=" * 76)
    print("SILABS AI FINAL TRAINING DATA BUILDER v1.2")
    print("=" * 76)

    chosen = []
    global_exact = set()
    stats = {}

    for dataset in CAPS:
        path = processed / f"{dataset}.jsonl"
        print(f"\n[{dataset}]")

        if not path.exists():
            print(" MISSING - skipped")
            stats[dataset] = {"status": "missing"}
            continue

        rows = read_jsonl(path)
        source = len(rows)
        self_copy = 0

        if dataset == "oasst1":
            has_raw_trees = any(
                (row.get("metadata") or {}).get("raw_prompt_tree")
                for row in rows
            )
            if has_raw_trees:
                rows, self_copy = flatten_oasst(rows)
                print(
                    f" Source {source:,} | extracted {len(rows):,} "
                    f"| self-copy rejected {self_copy:,}"
                )
            else:
                print(
                    f" Source {source:,} | using already-normalized OASST pairs"
                )

        before = len(rows)
        rows = [row for row in rows if quality(row)]
        bad = before - len(rows)
        input_duplicates = 0

        if dataset == "openmathinstruct2":
            rows, input_duplicates = dedup_input(rows)

        local = []
        seen = set()
        exact = 0

        for row in rows:
            key = digest(
                norm(row.get("input")) + "||" + norm(row.get("output"))
            )
            if key in seen:
                exact += 1
                continue
            seen.add(key)
            local.append(row)

        rows = local
        pre_cap = len(rows)
        rows = cap(rows, caps[dataset], args.seed, dataset)
        cap_removed = pre_cap - len(rows)

        keep = []
        cross_duplicates = 0
        for row in rows:
            key = digest(
                norm(row.get("input")) + "||" + norm(row.get("output"))
            )
            if key in global_exact:
                cross_duplicates += 1
                continue

            global_exact.add(key)
            row.setdefault("metadata", {})["finalizer_version"] = "1.2"
            keep.append(row)

        chosen += keep
        stats[dataset] = {
            "status": "ok",
            "source": source,
            "self_copy_rejected": self_copy,
            "quality_removed": bad,
            "input_duplicates_removed": input_duplicates,
            "exact_duplicates_removed": exact,
            "cap_removed": cap_removed,
            "cross_duplicates_removed": cross_duplicates,
            "selected": len(keep),
        }

        print(
            f" Selected {len(keep):,} | bad {bad:,} "
            f"| input-dups {input_duplicates:,} | exact-dups {exact:,} "
            f"| cap-removed {cap_removed:,} "
            f"| cross-dups {cross_duplicates:,}"
        )

    train, dev, split_stats = global_grouped_split(
        chosen,
        args.dev_ratio,
        args.seed,
    )

    train_inputs = {digest(norm(row.get("input"))) for row in train}
    dev_inputs = {digest(norm(row.get("input"))) for row in dev}
    leakage = len(train_inputs & dev_inputs)

    print(f"\nGlobal same-input leakage assertion: {leakage}")
    if leakage:
        raise SystemExit("FATAL: refusing to write split files.")

    write_jsonl(final / "train.jsonl", train)
    write_jsonl(final / "dev.jsonl", dev)

    report = {
        "version": "1.2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "dev_ratio": args.dev_ratio,
        "pq_status": "deferred",
        "caps": caps,
        "datasets": stats,
        "split_stats": split_stats,
        "total_finalized": len(chosen),
        "train_records": len(train),
        "dev_records": len(dev),
        "split_rule": "GLOBAL normalized-input grouping across all datasets",
        "same_input_leakage_assertion": leakage,
        "excluded": [
            "ai_vs_human",
            "mmlu_pro",
            "official validation/test",
            "unixpress_pq_for_now",
        ],
    }

    (reports / "final_training_data_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n" + "=" * 76)
    print("FINALIZATION SUMMARY")
    print("=" * 76)
    for dataset in CAPS:
        print(f"{dataset:20} {stats.get(dataset, {}).get('selected', 0):>8,}")
    print(
        "-" * 32
        + f"\n{'FINAL CORPUS':20} {len(chosen):>8,}"
        + f"\n{'TRAIN':20} {len(train):>8,}"
        + f"\n{'DEV':20} {len(dev):>8,}"
    )
    print("\nRESULT: v1.2 finalized with global input-group isolation.")


if __name__ == "__main__":
    main()
