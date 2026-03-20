#!/usr/bin/env python3
"""Retrieve and output Kaizen entities for Codex to filter."""

from __future__ import annotations

import argparse
import re

from entity_io import find_entities_dir, load_all_entities, log as _log


def log(message: str) -> None:
    _log("retrieve", message)


def normalize_words(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if len(word) > 3}


def relevance_score(entity: dict[str, str], task_words: set[str]) -> int:
    if not task_words:
        return 0
    entity_words = normalize_words(f"{entity.get('content', '')} {entity.get('trigger', '')}")
    return len(task_words & entity_words)


def format_entities(entities: list[dict[str, str]], entity_type: str) -> str:
    header = f"## KAIZEN {entity_type.upper()}S ({len(entities)} found)\n\nReview these entities and apply any relevant ones:\n\n"
    items = []
    for entity in entities:
        content = entity.get("content")
        if not content:
            continue
        item = f"- **[{entity.get('type', 'general')}]** {content}"
        if entity.get("rationale"):
            item += f"\n  - _Rationale: {entity['rationale']}_"
        if entity.get("trigger"):
            item += f"\n  - _When: {entity['trigger']}_"
        items.append(item)
    return header + "\n\n".join(items) + "\n\n--- END GUIDELINES ---"


def main() -> int:
    parser = argparse.ArgumentParser(description="Retrieve Kaizen entities.")
    parser.add_argument(
        "--type",
        default="guideline",
        help="Entity type to retrieve (default: guideline).",
    )
    parser.add_argument(
        "--task",
        default="",
        help="Task description used for lightweight relevance ordering.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of entities to return.",
    )
    args = parser.parse_args()

    entities_dir = find_entities_dir()
    log(f"Entities dir: {entities_dir}")

    if not entities_dir:
        print("No Kaizen entities exist yet. Complete some tasks to generate learnings!")
        return 0

    entities = load_all_entities(entities_dir)
    filtered = [entity for entity in entities if entity.get("type", "general") == args.type]

    if not filtered:
        print(f"No entities of type '{args.type}' found.")
        return 0

    task_words = normalize_words(args.task)
    filtered.sort(
        key=lambda entity: (
            relevance_score(entity, task_words),
            entity.get("content", ""),
        ),
        reverse=True,
    )
    results = filtered[: args.limit]
    print(format_entities(results, args.type))
    log(f"Returned {len(results)} entities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
