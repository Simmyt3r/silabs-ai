from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from datasets import load_dataset


DATASETS = {
    "oasst1": {
        "repo_id": "OpenAssistant/oasst1",
        "config": None,
        "split": "train",
        "license": "apache-2.0",
        "commercial_status": "allowed",
    },
    "gsm8k": {
        "repo_id": "openai/gsm8k",
        "config": "main",
        "split": "train",
        "license": "mit",
        "commercial_status": "allowed",
    },
    "arc_easy": {
        "repo_id": "allenai/ai2_arc",
        "config": "ARC-Easy",
        "split": "train",
        "license": "cc-by-sa-4.0",
        "commercial_status": "allowed_with_attribution_sharealike_review",
    },
    "arc_challenge": {
        "repo_id": "allenai/ai2_arc",
        "config": "ARC-Challenge",
        "split": "train",
        "license": "cc-by-sa-4.0",
        "commercial_status": "allowed_with_attribution_sharealike_review",
    },
    "sciq": {
        "repo_id": "allenai/sciq",
        "config": None,
        "split": "train",
        "license": "cc-by-nc-3.0",
        "commercial_status": "research_only",
    },
    "openbookqa": {
        "repo_id": "allenai/openbookqa",
        "config": "main",
        "split": "train",
        "license": "unknown",
        "commercial_status": "review_required",
    },
    "hotpotqa": {
        "repo_id": "hotpotqa/hotpot_qa",
        "config": "distractor",
        "split": "train",
        "license": "cc-by-sa-4.0",
        "commercial_status": "allowed_with_attribution_sharealike_review",
    },
    "openmathinstruct2": {
        "repo_id": "nvidia/OpenMathInstruct-2",
        "config": None,
        "split": "train_1M",
        "license": "cc-by-4.0",
        "commercial_status": "allowed_with_attribution",
    },
}

COMMERCIAL_EXCLUDE = {"sciq", "openbookqa"}


def clean(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return re.sub(r"\s+", " ", str(value)).strip()


def stable_id(dataset: str, input_text: str, output_text: str) -> str:
    payload = f"{dataset}\n{clean(input_text).lower()}\n{clean(output_text).lower()}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
    return f"{dataset}_{digest}"


def record(
    dataset: str,
    task: str,
    instruction: str,
    input_text: str,
    output_text: str,
    metadata: dict | None = None,
) -> dict:
    metadata = dict(metadata or {})
    metadata.setdefault("source_repo", DATASETS[dataset]["repo_id"])
    metadata.setdefault("source_split", DATASETS[dataset]["split"])
    metadata.setdefault("source_license", DATASETS[dataset]["license"])
    return {
        "id": stable_id(dataset, input_text, output_text),
        "dataset": dataset,
        "task": task,
        "domain": metadata.pop("domain", ""),
        "instruction": clean(instruction),
        "input": clean(input_text),
        "output": clean(output_text),
        "metadata": metadata,
    }


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            if not clean(row.get("input")) or not clean(row.get("output")):
                continue
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def load(name: str, *, streaming: bool = False):
    spec = DATASETS[name]
    kwargs = {
        "path": spec["repo_id"],
        "split": spec["split"],
        "streaming": streaming,
    }
    if spec["config"]:
        kwargs["name"] = spec["config"]
    return load_dataset(**kwargs)


def oasst_records() -> list[dict]:
    dataset = load("oasst1")
    rows = [dict(row) for row in dataset]
    by_id = {row.get("message_id"): row for row in rows if row.get("message_id")}
    output = []

    for row in rows:
        if clean(row.get("role")).lower() != "assistant":
            continue
        parent = by_id.get(row.get("parent_id"))
        if not parent:
            continue
        if clean(parent.get("role")).lower() not in {"prompter", "user", "human"}:
            continue

        prompt = clean(parent.get("text"))
        answer = clean(row.get("text"))
        if not prompt or not answer or prompt.lower() == answer.lower():
            continue

        output.append(
            record(
                "oasst1",
                "instruction_chat",
                "Respond helpfully and accurately to the user.",
                prompt,
                answer,
                {
                    "language": row.get("lang") or parent.get("lang") or "unknown",
                    "message_id": row.get("message_id"),
                    "parent_id": row.get("parent_id"),
                    "message_tree_id": row.get("message_tree_id"),
                    "quality": "public_unreviewed",
                },
            )
        )

    return output


def gsm8k_records() -> list[dict]:
    return [
        record(
            "gsm8k",
            "math_reasoning",
            "Solve the mathematics problem accurately.",
            row["question"],
            row["answer"],
            {"domain": "mathematics"},
        )
        for row in load("gsm8k")
    ]


def format_choices(question: str, labels, texts) -> str:
    lines = [clean(question), "", "Choices:"]
    for label, text_value in zip(labels, texts):
        lines.append(f"{clean(label)}. {clean(text_value)}")
    return "\n".join(lines)


def arc_records(name: str) -> list[dict]:
    output = []
    for row in load(name):
        choices = row.get("choices") or {}
        labels = choices.get("label") or []
        texts = choices.get("text") or []
        answer = clean(row.get("answerKey"))
        if not answer:
            continue
        output.append(
            record(
                name,
                "science_mcq",
                "Choose the correct answer. Reply with the option label only.",
                format_choices(row.get("question", ""), labels, texts),
                answer,
                {"domain": "science", "source_id": row.get("id")},
            )
        )
    return output


def sciq_records() -> list[dict]:
    output = []
    labels = ["A", "B", "C", "D"]

    for row in load("sciq"):
        question = clean(row.get("question"))
        correct = clean(row.get("correct_answer"))
        choices = [
            correct,
            clean(row.get("distractor1")),
            clean(row.get("distractor2")),
            clean(row.get("distractor3")),
        ]
        if not question or not all(choices):
            continue

        seed = int(hashlib.sha256(question.encode("utf-8")).hexdigest()[:16], 16)
        rng = random.Random(seed)
        rng.shuffle(choices)
        answer = labels[choices.index(correct)]

        output.append(
            record(
                "sciq",
                "science_mcq",
                "Choose the correct answer. Reply with the option label only.",
                format_choices(question, labels, choices),
                answer,
                {
                    "domain": "science",
                    "support": clean(row.get("support")),
                    "usage_restriction": "noncommercial",
                },
            )
        )

    return output


def openbookqa_records() -> list[dict]:
    output = []
    for row in load("openbookqa"):
        choices = row.get("choices") or {}
        labels = choices.get("label") or []
        texts = choices.get("text") or []
        answer = clean(row.get("answerKey"))
        if not answer:
            continue
        output.append(
            record(
                "openbookqa",
                "science_reasoning_mcq",
                "Choose the correct answer. Reply with the option label only.",
                format_choices(row.get("question_stem", ""), labels, texts),
                answer,
                {
                    "domain": "science",
                    "source_id": row.get("id"),
                    "license_review_required": True,
                },
            )
        )
    return output


def hotpot_context(value) -> str:
    if not isinstance(value, dict):
        return clean(value)
    titles = value.get("title") or []
    sentences = value.get("sentences") or []
    parts = []
    for title, sentence_group in zip(titles, sentences):
        body = " ".join(clean(sentence) for sentence in sentence_group)
        parts.append(f"{clean(title)}: {body}")
    return "\n".join(parts)


def hotpot_records(limit: int = 25000) -> list[dict]:
    stream = load("hotpotqa", streaming=True).shuffle(seed=42, buffer_size=10000)
    output = []
    seen_questions = set()

    for row in stream:
        question = clean(row.get("question"))
        answer = clean(row.get("answer"))
        key = question.lower()
        if not question or not answer or key in seen_questions:
            continue
        seen_questions.add(key)

        context = hotpot_context(row.get("context"))
        input_text = f"Question: {question}"
        if context:
            input_text += f"\n\nContext:\n{context}"

        output.append(
            record(
                "hotpotqa",
                "multi_hop_qa",
                "Answer the question accurately using the supplied context.",
                input_text,
                answer,
                {
                    "domain": "general_knowledge",
                    "source_id": row.get("id"),
                    "level": row.get("level"),
                    "question_type": row.get("type"),
                },
            )
        )
        if len(output) >= limit:
            break

    return output


def openmath_records(limit: int = 40000) -> list[dict]:
    stream = load("openmathinstruct2", streaming=True).shuffle(
        seed=42,
        buffer_size=10000,
    )
    output = []
    seen_problems = set()

    for row in stream:
        problem = clean(row.get("problem"))
        solution = clean(row.get("generated_solution"))
        key = problem.lower()
        if not problem or not solution or key in seen_problems:
            continue
        seen_problems.add(key)

        output.append(
            record(
                "openmathinstruct2",
                "math_reasoning",
                "Solve the mathematics problem accurately and show useful reasoning.",
                problem,
                solution,
                {
                    "domain": "mathematics",
                    "problem_source": row.get("problem_source"),
                    "expected_answer": clean(row.get("expected_answer")),
                },
            )
        )
        if len(output) >= limit:
            break

    return output


BUILDERS = {
    "oasst1": oasst_records,
    "gsm8k": gsm8k_records,
    "arc_easy": lambda: arc_records("arc_easy"),
    "arc_challenge": lambda: arc_records("arc_challenge"),
    "sciq": sciq_records,
    "openbookqa": openbookqa_records,
    "hotpotqa": hotpot_records,
    "openmathinstruct2": openmath_records,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and normalize public Silabs AI training datasets"
    )
    parser.add_argument(
        "--profile",
        choices=["research", "commercial"],
        default="research",
        help=(
            "research reproduces the historical 8-dataset corpus; commercial "
            "omits sources that are noncommercial or have unresolved licensing"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets/processed"),
    )
    args = parser.parse_args()

    selected = list(DATASETS)
    if args.profile == "commercial":
        selected = [name for name in selected if name not in COMMERCIAL_EXCLUDE]

    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": args.profile,
        "datasets": {},
    }

    print("=" * 76)
    print(f"SILABS AI DATASET DOWNLOAD - {args.profile.upper()} PROFILE")
    print("=" * 76)

    for name in selected:
        spec = DATASETS[name]
        print(f"\n[{name}] {spec['repo_id']} :: {spec['split']}")
        rows = BUILDERS[name]()
        path = args.output_dir / f"{name}.jsonl"
        count = write_jsonl(path, rows)
        manifest["datasets"][name] = {
            **spec,
            "records_written": count,
            "path": str(path),
        }
        print(f" wrote {count:,} records -> {path}")

    for name in DATASETS:
        if name not in selected:
            manifest["datasets"][name] = {
                **DATASETS[name],
                "records_written": 0,
                "status": "excluded_by_profile",
            }
            print(
                f"\n[{name}] SKIPPED for {args.profile} profile "
                f"({DATASETS[name]['commercial_status']})"
            )

    manifest_path = Path("reports") / "dataset_download_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("\nDOWNLOAD/NORMALIZATION COMPLETE")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
