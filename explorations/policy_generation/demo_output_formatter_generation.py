"""
Demo: OutputFormatter Policy Generation from Trajectory Response Patterns

This script demonstrates the MVP of auto-generating OutputFormatter policies
by analyzing recurring formatting patterns in agent trajectory responses.

Each cluster of trajectories below maps to a real OutputFormatter use case
from https://docs.cuga.dev/docs/sdk/policies/output-formatter/:

  Cluster 1 — Markdown: Agent always produces analysis/findings responses
               → should generate a "Structured Report" formatter
               (Executive Summary, Key Findings, Recommendations, Next Steps)

  Cluster 2 — JSON Schema: Agent returns data queries as freeform prose
               → should generate a "Structured Data Output" formatter
               ({status, data[], summary} JSON schema)

  Cluster 3 — Direct: Agent produces verbose error messages inconsistently
               → should generate an "Error Response Template" formatter
               (replace with a clean, user-friendly error string)

  Cluster 4 — Markdown + NL trigger: Agent produces undocumented technical
               content without consistent structure
               → should generate a "Technical Documentation" formatter
               (Title, Overview, Code blocks, Examples, References)

Usage:
    cd kaizen-lib
    set -a && source ../.env && set +a
    .venv/bin/python explorations/policy_generation/demo_output_formatter_generation.py

Requirements:
    - A configured LLM (set KAIZEN_TIPS_MODEL or defaults to gpt-4o)
    - kaizen-lib installed (pip install -e .)
"""

import json
import sys

from output_formatter import (
    TrajectoryResponse,
    generate_output_formatter_policies_from_responses,
)
from kaizen.schema.policy import Policy, PolicyType

# ---------------------------------------------------------------------------
# Cluster 1: Analysis/Report responses — inconsistent markdown structure.
# The agent is doing good analysis but formatting varies run to run.
# Expected outcome: Markdown formatter with Executive Summary + Key Findings
#                   + Recommendations + Next Steps.
# ---------------------------------------------------------------------------
REPORT_RESPONSES = [
    TrajectoryResponse(
        task_summary="Analyze Q3 sales performance across regions",
        final_answer="""\
The Q3 sales data shows mixed results. The North region outperformed by 12% while the South fell short by 8%.

Overall revenue was $4.2M vs $4.0M target. Top products were SKU-112 and SKU-205.

We should probably focus on the South region next quarter and double down on the top SKUs.
Maybe also look at why the West region was flat.""",
    ),
    TrajectoryResponse(
        task_summary="Review the marketing campaign effectiveness for Product X launch",
        final_answer="""\
The Product X campaign reached 1.2M impressions with a 3.4% CTR, above the 2.8% benchmark.

Conversion rate was 1.1% — below the 1.5% goal. Email channel outperformed paid social.
The influencer segment generated 40% of conversions despite only 15% of budget.

Action items: reallocate budget toward email and influencer, revisit landing page copy to improve conversion.""",
    ),
    TrajectoryResponse(
        task_summary="Assess the risk factors in the current supply chain",
        final_answer="""\
Three key risks identified: single-source dependency on Supplier A (60% of components),
shipping delays averaging 12 days vs 7-day SLA, and raw material cost volatility (+18% YoY).

The single-source risk is critical. Shipping delays are causing downstream stockouts.
Recommend qualifying two alternative suppliers by Q1, renegotiating SLA with current logistics partner,
and establishing a 45-day safety stock buffer for top-10 components.""",
    ),
    TrajectoryResponse(
        task_summary="Evaluate the performance of the new onboarding flow",
        final_answer="""\
New onboarding completion rate is 74% vs 61% for the old flow — a solid improvement.
Drop-off still concentrated at step 3 (payment setup, 18% abandon).

Users who complete onboarding show 2.3x higher 30-day retention.
Next steps: simplify the payment step, add a progress indicator, and A/B test skipping payment until first use.""",
    ),
]

REPORT_FEEDBACK = [
    "Reports should always start with an Executive Summary of 2-3 sentences",
    "Key Findings should be presented as bullet points",
    "Each report must include a Recommendations section with numbered items",
    "Next Steps should be listed as concrete action items",
]

# ---------------------------------------------------------------------------
# Cluster 2: Data query responses — agent returns results as freeform prose
# instead of structured data. API consumers need parseable JSON.
# Expected outcome: JSON Schema formatter with {status, data[], summary}.
# ---------------------------------------------------------------------------
DATA_RESPONSES = [
    TrajectoryResponse(
        task_summary="Fetch all active users created in the last 30 days",
        final_answer="""\
I found 3 active users created in the last 30 days. They are Alice Johnson (alice@example.com, created Jan 5),
Bob Smith (bob@example.com, created Jan 12), and Carol White (carol@example.com, created Jan 19).
The query completed successfully.""",
    ),
    TrajectoryResponse(
        task_summary="List all open support tickets assigned to the platform team",
        final_answer="""\
There are 2 open tickets for the platform team. Ticket #4421 is titled 'API rate limit errors'
and was opened on Jan 8. Ticket #4398 is titled 'Database connection timeouts' and was opened on Jan 3.
Both are in progress.""",
    ),
    TrajectoryResponse(
        task_summary="Retrieve inventory levels for all products below reorder threshold",
        final_answer="""\
Query successful. Found 2 products below reorder threshold: SKU-112 has 45 units remaining
(threshold: 100), and SKU-089 has 12 units remaining (threshold: 50).
Immediate reorder is recommended for SKU-089.""",
    ),
    TrajectoryResponse(
        task_summary="Get all failed transactions from the payment system in the last 24 hours",
        final_answer="""\
Retrieved 2 failed transactions from the last 24 hours. Transaction TXN-9981 failed at 02:14 UTC
for $149.99 due to insufficient funds. Transaction TXN-9994 failed at 11:38 UTC for $89.00 due
to card declined. Overall status: query completed, 2 records returned.""",
    ),
]

DATA_FEEDBACK = [
    "API consumers require JSON responses with 'status', 'data', and 'summary' fields",
    "The 'data' field must be an array of objects, not freeform prose",
    "All data query responses must be machine-parseable JSON",
]

# ---------------------------------------------------------------------------
# Cluster 3: Error responses — agent produces verbose, inconsistent error
# messages that expose internal details or vary in tone.
# Expected outcome: Direct formatter replacing error responses with a clean
#                   user-friendly template string.
# ---------------------------------------------------------------------------
ERROR_RESPONSES = [
    TrajectoryResponse(
        task_summary="Fetch user profile for user ID 9999",
        final_answer="""\
Error: DatabaseConnectionException - Failed to connect to primary replica after 3 retries.
Last attempt: 2024-01-15T10:23:44Z. Connection pool exhausted (max: 20, active: 20).
Please check the database configuration or try again later.""",
    ),
    TrajectoryResponse(
        task_summary="Process payment for order #ORD-77321",
        final_answer="""\
An unexpected error occurred while calling the payment gateway.
Exception: PaymentGatewayTimeoutException at PaymentService.java:142.
Transaction was not completed. The payment provider returned HTTP 504.
Internal reference: ERR-20240115-0042.""",
    ),
    TrajectoryResponse(
        task_summary="Generate monthly report for account ACC-5512",
        final_answer="""\
Failed to generate report. NullPointerException encountered in ReportBuilder module.
Stack trace logged under request ID req-8821-a. Data for ACC-5512 may be incomplete.
Contact your system administrator if this persists.""",
    ),
    TrajectoryResponse(
        task_summary="Send notification to user group BETA_TESTERS",
        final_answer="""\
Could not deliver notifications. SMTP connection refused on port 587.
Error code: CONN_REFUSED. Notification job ID: job-4421 has been marked as failed.
Retry policy: 3 attempts exhausted. Check email service configuration.""",
    ),
]

ERROR_FEEDBACK = [
    "Error messages must never expose internal exception types, stack traces, or system details",
    "All error responses should use a consistent, user-friendly tone",
    "Users should be directed to contact support, not told to check system configuration",
]

# ---------------------------------------------------------------------------
# Cluster 4: Technical content responses — agent explains APIs, code, and
# developer concepts but without consistent documentation structure.
# Expected outcome: Markdown formatter with Title, Overview, Code blocks,
#                   Examples, References — triggered by NL similarity.
# ---------------------------------------------------------------------------
TECH_DOC_RESPONSES = [
    TrajectoryResponse(
        task_summary="Explain how to use the /search endpoint of the Kaizen API",
        final_answer="""\
The search endpoint lets you query entities by vector similarity. You pass a query string
and it returns the top-k most similar entities. You need to set the namespace_id parameter.

You'd call it like: POST /api/v1/search with body {"query": "...", "namespace_id": "...", "top_k": 5}

It uses cosine similarity under the hood. The response includes entity content and a similarity score.
Make sure your API key is in the Authorization header.""",
    ),
    TrajectoryResponse(
        task_summary="Document the save_trajectory MCP tool",
        final_answer="""\
save_trajectory is an MCP tool that persists agent execution trajectories to Kaizen.
It takes a messages list (OpenAI format), a namespace_id, and optional metadata.

Usage: call save_trajectory(messages=[...], namespace_id="my-namespace", metadata={"task": "..."})

It calls parse_openai_agents_trajectory internally to extract task instruction and steps,
then stores the result as a Kaizen entity with type="trajectory". Returns the entity ID on success.""",
    ),
    TrajectoryResponse(
        task_summary="Describe how OutputFormatter policies work in CUGA",
        final_answer="""\
OutputFormatter policies transform final AI responses before returning them to users.
They are checked after the agent generates its final answer.

Three format types: markdown (LLM reformats using instructions), json_schema (LLM outputs valid JSON),
and direct (no LLM — response is replaced with a static string).

Triggers check the content of the agent's response using keyword or natural language matching.
When a trigger matches, the formatter is applied. If multiple match, highest priority wins.

To add one: agent.policies.add_output_formatter(name=..., format_type=..., format_config=..., keywords=[...])""",
    ),
    TrajectoryResponse(
        task_summary="Explain the Kaizen entity storage model",
        final_answer="""\
Kaizen stores all data as Entity objects. Each entity has content (string), type (string),
and optional metadata (dict). Entities are embedded and stored in Milvus for vector search.

The Entity model has: id (auto-generated UUID), content, type, metadata, created_at.
RecordedEntity extends Entity with the id and timestamp fields.

You create entities via the KaizenClient or MCP tools. The backend (Milvus or filesystem)
handles embedding generation automatically. Use get_entities() to retrieve by type or search semantically.""",
    ),
]

TECH_DOC_FEEDBACK = [
    "Technical responses should follow a consistent documentation structure with a title",
    "Code examples should always be in fenced code blocks",
    "Responses about APIs or tools should include an Overview, a Usage/Examples section, and References",
    "Documentation responses lack consistent structure — readers cannot skim headings",
]


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

CLUSTERS = [
    {
        "name": "Cluster 1 — Analysis Reports (Markdown formatter)",
        "responses": REPORT_RESPONSES,
        "feedback": REPORT_FEEDBACK,
    },
    {
        "name": "Cluster 2 — Data Query Results (JSON Schema formatter)",
        "responses": DATA_RESPONSES,
        "feedback": DATA_FEEDBACK,
    },
    {
        "name": "Cluster 3 — Error Messages (Direct formatter)",
        "responses": ERROR_RESPONSES,
        "feedback": ERROR_FEEDBACK,
    },
    {
        "name": "Cluster 4 — Technical Documentation (Markdown + NL trigger)",
        "responses": TECH_DOC_RESPONSES,
        "feedback": TECH_DOC_FEEDBACK,
    },
]


def main():
    print("=" * 70)
    print("  OutputFormatter Policy Generation — MVP Demo")
    print("=" * 70)
    print()

    all_policies: list[Policy] = []

    for cluster in CLUSTERS:
        print(f"{'─' * 70}")
        print(f"  {cluster['name']}")
        print(f"{'─' * 70}")
        print(f"  Trajectories: {len(cluster['responses'])}  |  Feedback items: {len(cluster['feedback'])}")
        print()
        print("  Calling LLM to analyze response patterns...")
        print()

        suggestions = generate_output_formatter_policies_from_responses(
            responses=cluster["responses"],
            evaluation_feedback=cluster["feedback"],
        )

        if not suggestions:
            print("  ⚠️  No suggestions generated — check LLM configuration.")
            continue

        # Pick the top suggestion (highest confidence)
        top = max(suggestions, key=lambda s: s.confidence)

        print(f"  Generated {len(suggestions)} suggestion(s). Top suggestion:")
        print(f"    Name:        {top.name}")
        print(f"    Confidence:  {top.confidence:.0%}")
        print(f"    Format type: {top.config.get('format_type', 'N/A')}")
        print(f"    Description: {top.description}")
        print(f"    Evidence:    {top.evidence}")
        print(f"    Triggers:    {len(top.triggers)} trigger(s)")
        for t in top.triggers:
            print(f"      - [{t.type}] target={t.target}, value={t.value}")
        print(f"    Content preview:")
        content_preview = top.content[:250] + ("..." if len(top.content) > 250 else "")
        for line in content_preview.split("\n"):
            print(f"      {line}")
        print()

        # Convert to Kaizen Policy
        policy = Policy(
            name=top.name,
            type=PolicyType.OUTPUT_FORMATTER,
            description=top.description,
            triggers=top.triggers,
            content=top.content,
            config=top.config,
            priority=50,
            enabled=False,  # Draft mode — requires human review
        )
        all_policies.append(policy)

    # ---------------------------------------------------------------------------
    # Final summary: all generated Kaizen Policy entities
    # ---------------------------------------------------------------------------
    print("=" * 70)
    print(f"  Summary: {len(all_policies)} OutputFormatter policies generated")
    print("=" * 70)
    print()

    for i, policy in enumerate(all_policies, 1):
        print(f"--- Policy {i}: {policy.name} ---")
        print(json.dumps(policy.model_dump(mode="json"), indent=2))
        print()

    print("=" * 70)
    print("  Demo complete!")
    print()
    print("  All policies are in draft mode (enabled=False).")
    print("  Next steps in a real deployment:")
    print("  1. Store each policy in Kaizen via create_entity(type='policy')")
    print("  2. An admin reviews and enables the policies")
    print("  3. CUGA's KaizenPolicySource loads them at runtime")
    print("  4. Agent responses matching each trigger get auto-formatted")
    print("=" * 70)


if __name__ == "__main__":
    main()
