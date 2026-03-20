#!/usr/bin/env python3
"""Save Kaizen entities from stdin JSON into markdown files."""

from __future__ import annotations

import json
import sys

from entity_io import (
    find_entities_dir,
    get_default_entities_dir,
    load_all_entities,
    log as _log,
    write_entity_file,
)


def log(message: str) -> None:
    _log("save", message)


def normalize(text: str) -> str:
    """Normalize text for dedup comparison."""
    return " ".join(text.lower().split())


def main() -> int:
    if len(sys.argv) > 1:
        print("Error: save_entities.py does not accept CLI arguments.", file=sys.stderr)
        return 1

    try:
        input_data = json.load(sys.stdin)
        log(f"Received input with keys: {list(input_data.keys())}")
    except json.JSONDecodeError as exc:
        log(f"Failed to parse JSON input: {exc}")
        print(f"Error: Invalid JSON input - {exc}", file=sys.stderr)
        return 1

    new_entities = input_data.get("entities", [])
    if not new_entities:
        log("No entities in input")
        print("No entities provided in input.", file=sys.stderr)
        return 0

    entities_dir = find_entities_dir()
    if entities_dir:
        entities_dir = entities_dir.resolve()
        log(f"Found existing dir: {entities_dir}")
        print(f"Using existing entities dir: {entities_dir}")
    else:
        entities_dir = get_default_entities_dir()
        log(f"Created new dir: {entities_dir}")
        print(f"Created new entities dir: {entities_dir}")

    existing_entities = load_all_entities(entities_dir)
    existing_contents = {normalize(entity["content"]) for entity in existing_entities if entity.get("content")}

    added_count = 0
    for entity in new_entities:
        content = entity.get("content")
        if not content:
            continue
        if normalize(content) in existing_contents:
            log(f"Skipping duplicate: {content[:60]}")
            continue

        storable_entity = {
            "content": content,
            "rationale": entity.get("rationale", ""),
            "type": entity.get("type", "guideline"),
            "trigger": entity.get("trigger", ""),
        }

        path = write_entity_file(entities_dir, storable_entity)
        existing_contents.add(normalize(content))
        added_count += 1
        log(f"Wrote: {path}")

    total = len(existing_entities) + added_count
    log(f"Added {added_count} new entities. Total: {total}")
    print(f"Added {added_count} new entity(ies). Total: {total}")
    print(f"Entities stored in: {entities_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
