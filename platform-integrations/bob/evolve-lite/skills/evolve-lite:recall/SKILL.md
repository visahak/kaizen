---
name: recall
description: Retrieves relevant entities from a knowledge base to inject context-appropriate entities before task execution.
---

# Entity Retrieval

## Overview

This skill retrieves relevant entities from a stored knowledge base based on the current task context. Read all stored entities from the entities directory and apply any relevant ones to the current task.

Entities can come from multiple sources:
- **Private entities**: Your own local entities (not shared)
- **Public entities**: Your own entities marked for sharing
- **Subscribed entities**: Entities from other users you've subscribed to

## How It Works

1. The script scans `.evolve/entities/` and `.evolve/public/` and emits a compact manifest containing only `path`, `type`, and `trigger` for each entity
2. Review the manifest and identify entities whose trigger looks relevant to the current task
3. Use `read_file` to read the full content of relevant entity files on demand
4. Apply the retrieved guidance as additional context for your work

**Directory structure**:
- `.evolve/entities/guideline/` - Your private entities
- `.evolve/entities/subscribed/{name}/` - Mirrored entities from subscriptions
- `.evolve/public/guideline/` - Your published entities

## Usage

```bash
python3 scripts/retrieve_entities.py
```

This retrieves all entities from all sources (private, public, and subscribed).

## Entities Storage

Entities are stored as individual markdown files in `.evolve/entities/`, organized by source:

```text
.evolve/entities/
  guideline/                    # Private entities
    use-context-managers.md
  public/                       # Your published entities
    guideline/
      cache-api-responses.md
  subscribed/                   # Entities from others
    alice/
      guideline/
        error-handling.md
    bob-team/
      policy/
        code-review.md
```

The manifest output is human-readable:

```
- `.evolve/entities/guideline/use-context-managers.md` [guideline] — When processing files or managing resources
- `.evolve/entities/subscribed/alice/guideline/error-handling.md` [guideline] — When writing error handlers
```

Each file still uses markdown with YAML frontmatter:

```markdown
---
type: guideline
trigger: When processing files or managing resources
visibility: private
owner: alice
---

Use context managers for file operations

## Rationale

Ensures proper resource cleanup
```

## On-Demand Expansion

When a manifest entry's trigger matches the current task, use `read_file` to load the full entity. The file body contains the guideline content and an optional `## Rationale` section.
