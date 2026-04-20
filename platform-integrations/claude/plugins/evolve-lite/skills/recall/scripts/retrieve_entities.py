#!/usr/bin/env python3
"""Emit a compact manifest of stored entities.

Invoked by the recall skill. Lists one line per entity (path, type, slug,
source, trigger) without loading body content. Claude decides which files
to Read based on the manifest, so full-entity cost is paid only on demand
instead of on every user prompt.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "lib"))
from entity_io import find_entities_dir, get_evolve_dir, load_manifest, log as _log


def log(message):
    _log("retrieve", message)


def format_manifest(entries):
    """Format manifest lines for Claude to review."""
    header = (
        "## Available entities\n\n"
        "Stored guidelines and preferences are listed below. For any whose "
        "trigger matches the current task, use the Read tool with the "
        "provided path to load full content.\n\n"
    )
    if not entries:
        return header + "(none)"
    lines = []
    for e in entries:
        slug = e.get("slug", "")
        etype = e.get("type", "general")
        trigger = e.get("trigger") or "(no trigger)"
        source = e.get("source")
        tag = f" [from: {source}]" if source else ""
        path = e.get("path", "")
        lines.append(f"- `{path}` • {etype} • {slug}{tag} • {trigger}")
    return header + "\n".join(lines)


def main():
    log("Script started")
    entries = []

    entities_dir = find_entities_dir()
    if entities_dir:
        log(f"Loading manifest from: {entities_dir}")
        entries += load_manifest(entities_dir)

    public_dir = get_evolve_dir() / "public"
    if public_dir.is_dir():
        log(f"Loading manifest from: {public_dir}")
        entries += load_manifest(public_dir)

    log(f"Manifest entries: {len(entries)}")
    print(format_manifest(entries))


if __name__ == "__main__":
    main()
