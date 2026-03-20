---
name: kaizen-workflow
description: Run the Kaizen recall -> work -> learn workflow for substantive coding, debugging, implementation, and repository investigation tasks. Do not use for trivial conversational turns.
---

# Kaizen Workflow

Use this skill for substantive repository work where Kaizen guidance should shape the task.

## Goal

Coordinate the Kaizen flow in this exact order:

1. Recall existing guidance
2. Do the work
3. Learn from the task before finishing

## Required Sequence

1. If you have not already read the helper skill instructions in this conversation, read:
   - `$kaizen-recall`
   - `$kaizen-learn`
2. Invoke `$kaizen-recall` before other substantive work.
3. Complete the user's request, applying relevant recalled guidance when it matters.
4. Before your final response, invoke `$kaizen-learn`.
5. Only finish after the learn step has been considered.

## Notes

- Do not skip or reorder the workflow.
- If recall returns no entities, continue normally.
- If learn finds no high-signal entities, that counts as success.
- The final saved entities should be non-obvious, environment-specific, and grounded in what actually happened during the task.
