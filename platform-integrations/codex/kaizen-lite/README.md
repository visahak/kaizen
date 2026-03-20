# Kaizen Lite Skills for Codex

This directory contains a Codex-native version of the Kaizen Lite workflow.

Unlike the Claude Code integration, Codex does not currently expose the same plugin hook model, and unlike Roo it does not use custom modes in the same way. The Codex version therefore packages Kaizen as:

1. A repo-local `AGENTS.md` block that tells Codex to use Kaizen for substantive tasks
2. A `kaizen-workflow` skill that coordinates `recall -> work -> learn`
3. Two helper skills, `kaizen-recall` and `kaizen-learn`

## Quick Install

Install into the current repository's existing `AGENTS.md` and `.agents/skills` locations:

```bash
./platform-integrations/codex/kaizen-lite/install.sh
```

By default the script installs into this repository root. To target a different repo root:

```bash
./platform-integrations/codex/kaizen-lite/install.sh /path/to/repo-root
```

## What Gets Installed

- `kaizen-workflow`: top-level workflow skill that drives `recall -> work -> learn`
- `kaizen-recall`: retrieve relevant guidelines from `.kaizen/entities/` before starting work
- `kaizen-learn`: extract and save new guidelines into `.kaizen/entities/` after the task
- `AGENTS.md` Kaizen block: merged into the existing repo `AGENTS.md` using markers, not full-file overwrite

For Codex, helper logic is intentionally duplicated inside each skill's `scripts/` directory. That lets the integration reuse the Claude-compatible `retrieve_entities.py`, `save_entities.py`, and `entity_io.py` naming without depending on a special shared `lib/` directory under `.agents`.

## Recommended Workflow Setup

The installer is designed for repositories that already have an `AGENTS.md` and `.agents/` directory. It preserves existing content:

1. Existing non-Kaizen `AGENTS.md` instructions remain intact
2. A Kaizen block is appended or updated between markers
3. Existing non-Kaizen skills under `.agents/skills` are left alone

## Storage Format

This Codex integration reuses the Claude plugin's markdown entity storage:

```text
.kaizen/
  entities/
    guideline/
      use-python-pil-for-image-metadata-extraction.md
      cache-api-responses-locally.md
```

Each entity file contains markdown with YAML frontmatter:

```markdown
---
type: guideline
trigger: When extracting image metadata in containerized or sandboxed environments
---

Use Python PIL/Pillow for image metadata extraction in sandboxed environments

## Rationale

System tools may be unavailable
```

## Usage

`kaizen-workflow` is the skill that should auto-trigger for substantive tasks. It then explicitly invokes the two helper skills below.

### Recall helper

```bash
python3 .agents/skills/kaizen-recall/scripts/retrieve_entities.py --type guideline --task "brief task summary"
```

### Learn helper

```bash
printf '{"entities": [...]}' | python3 .agents/skills/kaizen-learn/scripts/save_entities.py
```

See each `SKILL.md` for the prompt-side workflow and quality bar.

## Source Layout

```text
platform-integrations/codex/kaizen-lite/
├── README.md
├── AGENTS.kaizen.md
├── install.sh
└── skills/
    ├── kaizen-workflow/
    │   ├── SKILL.md
    │   └── agents/
    │       └── openai.yaml
    ├── kaizen-learn/
    │   ├── agents/
    │   │   └── openai.yaml
    │   ├── SKILL.md
    │   └── scripts/
    │       ├── entity_io.py
    │       └── save_entities.py
    └── kaizen-recall/
        ├── agents/
        │   └── openai.yaml
        ├── SKILL.md
        └── scripts/
            ├── entity_io.py
            └── retrieve_entities.py
```

## Installed Layout

```text
<repo-root>/
├── AGENTS.md
└── .agents/
    └── skills/
        ├── ...existing skills...
        ├── kaizen-workflow/
        ├── kaizen-learn/
        └── kaizen-recall/
```

## Verification

After installation into a repo:

1. Restart or reopen the Codex session so it reloads repo-local `AGENTS.md` and `.agents/skills`.
2. Confirm the repo now has `.agents/skills/kaizen-workflow`, `.agents/skills/kaizen-recall`, and `.agents/skills/kaizen-learn`.
3. Confirm `AGENTS.md` contains a Kaizen block between `BEGIN KAIZEN CODEX` and `END KAIZEN CODEX`.
4. Start a substantive task and verify Codex follows the workflow.
