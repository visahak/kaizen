---
name: recall
description: Retrieves relevant entities from a knowledge base. A compact manifest is auto-injected on every user prompt via a UserPromptSubmit hook; Claude Reads the full body of only the entities whose triggers match the current task.
context: fork
---

# Entity Retrieval

## How it works

On every user prompt, the `UserPromptSubmit` hook runs:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/recall/scripts/retrieve_entities.py
```

The script scans `.evolve/entities/` (private + `subscribed/{name}/…`) and `.evolve/public/`, parses only YAML frontmatter (not bodies), and prints a compact manifest to stdout. Claude Code injects that stdout as context before Claude sees the prompt.

Each manifest line has the form:

```
- `<path>` • <type> • <slug> [from: <source>]? • <trigger>
```

- `path` — absolute or cwd-relative path to the entity markdown file.
- `type` — `guideline`, `preference`, etc.
- `slug` — filename stem.
- `[from: <source>]` — present only for entities subscribed from another user.
- `trigger` — the condition the entity applies to, or `(no trigger)`.

## What Claude does with the manifest

1. Scans the manifest for triggers that match the current task.
2. Uses the Read tool on the `path` of each matching entity to load the full body + rationale.
3. Applies the matching guidelines or preferences while working.

Baseline per-prompt cost is ~20–40 tokens per entity (manifest line). Full-body cost is paid only for entities Claude decides to Read.

## Why this design

The previous version of this hook emitted full entity bodies on every prompt, which grew linearly with both the entity count and the number of subscriptions. The manifest-only design keeps Claude aware of every stored entity while bounding per-prompt cost, so subscriptions and long-lived knowledge bases stay cheap to carry around.

## Storage layout

```text
.evolve/entities/
  guideline/
    use-context-managers-for-file-operations.md   ← private
  subscribed/
    alice/
      guideline/
        alice-tip.md                              ← annotated [from: alice]

.evolve/public/
  guideline/
    published-tip.md                              ← your own public, no annotation
```

Each file uses markdown with YAML frontmatter:

```markdown
---
type: guideline
trigger: When processing files or managing resources
---

Use context managers for file operations

## Rationale

Ensures proper resource cleanup
```
