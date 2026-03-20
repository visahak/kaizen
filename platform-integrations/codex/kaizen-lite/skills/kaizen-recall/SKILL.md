---
name: kaizen-recall
description: Retrieve relevant Kaizen entities from the current workspace before starting substantive work. Use this when orchestrated by kaizen-workflow or when you explicitly need to recall stored guidance.
---

# Kaizen Recall

Use this skill at the start of a coding, debugging, or repository investigation task.

## Goal

Fetch previously learned Kaizen entities from the current workspace's `.kaizen/entities/` directory so you can apply them before doing work.

## Execution

Resolve `scripts/retrieve_entities.py` relative to this skill directory, then run:

```bash
python3 scripts/retrieve_entities.py --type guideline --task "<brief summary of the user's goal>"
```

If `python3` is unavailable, use `python`.

Required parameters:

- `--type guideline`
- `--task "<brief summary>"`

## Notes

- The script reads from the current workspace, not from the skill directory.
- If no guidelines are found, proceed normally.
- Review the returned guidelines and apply any relevant ones to the task.
