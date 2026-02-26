# Policy Generation from Trajectories — Exploration

MVP exploration for auto-generating Kaizen policies by analyzing recurring
patterns in agent trajectory responses.

See the full design proposal in `docs/policy_generation_from_trajectories.md`.

---

## OutputFormatter Demo

Demonstrates how 4 clusters of agent trajectories — each representing a
different formatting problem — are automatically analyzed to produce
`OutputFormatter` policy suggestions ready for human review.

Each cluster maps to a real use case from the
[OutputFormatter docs](https://docs.cuga.dev/docs/sdk/policies/output-formatter/):

| Cluster | Format type | Problem |
|---------|-------------|---------|
| 1 — Analysis Reports | `markdown` | Agent produces unstructured analysis prose |
| 2 — Data Queries | `json_schema` | Agent returns query results as freeform text |
| 3 — Error Messages | `direct` | Agent leaks internal exceptions to users |
| 4 — Technical Docs | `markdown` + NL trigger | Agent explains APIs without consistent structure |

### Prerequisites

- Python 3.12+
- `kaizen-lib` installed (`pip install -e .` from the `kaizen-lib` directory)
- A configured LLM — set `KAIZEN_TIPS_MODEL` in your `.env` file

### Run

```bash
cd kaizen-lib
set -a && source ../.env && set +a
.venv/bin/python explorations/policy_generation/demo_output_formatter_generation.py
```

### What you'll see

For each cluster the demo will print:
- The top policy suggestion detected by the LLM (name, confidence, format type, triggers, content preview)
- The full Kaizen `Policy` JSON that would be stored, with `enabled: false` (draft mode)

All generated policies require **explicit human approval** before they take effect.
An admin reviews the suggestions and enables the ones that look correct.

### Extending the demo

To add your own trajectory cluster, define a list of `TrajectoryResponse` objects
and optional `evaluation_feedback` strings, then append a new entry to `CLUSTERS`
in `demo_output_formatter_generation.py`:

```python
from explorations.policy_generation.output_formatter import TrajectoryResponse

MY_RESPONSES = [
    TrajectoryResponse(
        task_summary="...",
        final_answer="...",
    ),
    ...
]

MY_FEEDBACK = [
    "Responses should always ...",
]
```
