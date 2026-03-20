#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_SKILLS_DIR="$SCRIPT_DIR/skills"
TARGET_REPO_ROOT="${1:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
TARGET_SKILLS_DIR="$TARGET_REPO_ROOT/.agents/skills"
TARGET_AGENTS_FILE="$TARGET_REPO_ROOT/AGENTS.md"
KAIZEN_BLOCK_SOURCE="$SCRIPT_DIR/AGENTS.kaizen.md"
KAIZEN_BLOCK_BEGIN="<!-- BEGIN KAIZEN CODEX -->"
KAIZEN_BLOCK_END="<!-- END KAIZEN CODEX -->"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
PYTHON_BIN="$(command -v python3 || command -v python || true)"

echo "== Kaizen Lite Codex Installer =="
echo

if [ ! -d "$SOURCE_SKILLS_DIR" ]; then
    echo "Error: source skills directory not found: $SOURCE_SKILLS_DIR" >&2
    exit 1
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "Error: python3 or python is required to merge the Kaizen AGENTS block." >&2
    exit 1
fi

mkdir -p "$TARGET_SKILLS_DIR"

install_skill() {
    local skill_name="$1"
    local source_dir="$SOURCE_SKILLS_DIR/$skill_name"
    local dest_dir="$TARGET_SKILLS_DIR/$skill_name"

    if [ ! -d "$source_dir" ]; then
        echo "Warning: missing source skill: $skill_name" >&2
        return 1
    fi

    if [ -d "$dest_dir" ]; then
        local backup_dir="${dest_dir}.backup.${TIMESTAMP}"
        echo "Backing up existing $skill_name to $backup_dir"
        mv "$dest_dir" "$backup_dir"
    fi

    cp -R "$source_dir" "$dest_dir"
    echo "Installed $skill_name -> $dest_dir"
}

merge_agents_block() {
    local temp_block
    temp_block="$(mktemp)"

    {
        printf "%s\n" "$KAIZEN_BLOCK_BEGIN"
        cat "$KAIZEN_BLOCK_SOURCE"
        printf "\n%s\n" "$KAIZEN_BLOCK_END"
    } > "$temp_block"

    if [ ! -f "$TARGET_AGENTS_FILE" ]; then
        cp "$temp_block" "$TARGET_AGENTS_FILE"
        echo "Created $TARGET_AGENTS_FILE"
        rm -f "$temp_block"
        return
    fi

    local backup_file="${TARGET_AGENTS_FILE}.backup.${TIMESTAMP}"
    cp "$TARGET_AGENTS_FILE" "$backup_file"
    echo "Backed up existing AGENTS.md to $backup_file"

    "$PYTHON_BIN" - "$TARGET_AGENTS_FILE" "$temp_block" "$KAIZEN_BLOCK_BEGIN" "$KAIZEN_BLOCK_END" <<'PY'
from __future__ import annotations

import pathlib
import sys

agents_path = pathlib.Path(sys.argv[1])
block_path = pathlib.Path(sys.argv[2])
begin = sys.argv[3]
end = sys.argv[4]

agents_text = agents_path.read_text(encoding="utf-8")
block_text = block_path.read_text(encoding="utf-8").rstrip() + "\n"

if begin in agents_text and end in agents_text:
    start = agents_text.index(begin)
    finish = agents_text.index(end, start) + len(end)
    updated = agents_text[:start].rstrip() + "\n\n" + block_text + agents_text[finish:]
else:
    updated = agents_text.rstrip() + "\n\n" + block_text

agents_path.write_text(updated.rstrip() + "\n", encoding="utf-8")
PY

    echo "Merged Kaizen block into $TARGET_AGENTS_FILE"
    rm -f "$temp_block"
}

for skill_dir in "$SOURCE_SKILLS_DIR"/*; do
    if [ -d "$skill_dir" ]; then
        install_skill "$(basename "$skill_dir")"
    fi
done

merge_agents_block

echo
echo "Install complete."
echo "Next steps:"
echo "1. Restart or reopen the Codex session so it reloads repo-local skills and AGENTS.md."
echo "2. Confirm $TARGET_REPO_ROOT/.agents/skills contains kaizen-workflow, kaizen-recall, and kaizen-learn."
echo "3. For a substantive task, Codex should now follow kaizen-workflow -> recall -> work -> learn."
