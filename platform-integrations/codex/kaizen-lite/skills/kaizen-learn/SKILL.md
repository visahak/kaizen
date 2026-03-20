---
name: kaizen-learn
description: Extract and save high-signal Kaizen entities from the completed task before finishing. Use this when orchestrated by kaizen-workflow or when you explicitly want to save learnings.
---

# Kaizen Learn

Use this skill near the end of a substantive task, before you wrap up.

## Goal

Reflect on the work that just happened and save only the non-obvious, reusable learnings that would help on similar tasks in the future.

## What To Look For

Focus on real discoveries from the current task:

- tool failures or permission errors
- wrong initial approaches that were later corrected
- retry loops that revealed a better default path
- project-specific workflow details
- environment-specific constraints

Do not save generic advice a competent coding agent would already know.

## Quality Gate

Only save a learning if it is:

1. Non-obvious
2. Specific to this environment, workflow, or codebase
3. Grounded in something that actually happened during the task

If nothing passes that bar, output `{"entities": []}` and treat that as success.

## Output Format

Generate JSON like this:

```json
{
  "entities": [
    {
      "content": "Proactive recommendation stating what to do",
      "rationale": "Why this approach works better",
      "type": "guideline",
      "trigger": "Situational context where this applies"
    }
  ]
}
```

Return 0-2 entities. Zero is valid.

## Save Step

Resolve `scripts/save_entities.py` relative to this skill directory, then pipe the JSON into:

```bash
printf '{"entities": [...]}' | python3 scripts/save_entities.py
```

If `python3` is unavailable, use `python`.

Important:

- `save_entities.py` reads JSON from stdin only.
- Do not pass CLI flags to `save_entities.py`.
- Review the script output to confirm whether anything was saved.
