"""
Generate OutputFormatter policy suggestions from agent trajectory responses.

This module analyzes final answers across multiple trajectories to detect
recurring formatting patterns, then proposes OutputFormatter policies.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import litellm
from jinja2 import Template
from litellm import completion, get_supported_openai_params, supports_response_schema

from kaizen.config.llm import llm_settings
from kaizen.llm.tips.tips import parse_openai_agents_trajectory
from kaizen.schema.policy import PolicyGenerationResponse, PolicySuggestion
from kaizen.utils.utils import clean_llm_response


@dataclass
class TrajectoryResponse:
    """A single trajectory's final response data for pattern analysis."""

    task_summary: str
    final_answer: str


def extract_responses_from_trajectories(
    trajectories: list[list[dict]],
) -> list[TrajectoryResponse]:
    """
    Extract final answers from raw trajectory message lists.

    Each trajectory is a list of messages (as returned by OpenAI Agents SDK's
    streamer.to_input_list()). The last assistant message with string content
    is treated as the final answer.

    Args:
        trajectories: List of raw trajectory message lists.

    Returns:
        List of TrajectoryResponse objects with task summaries and final answers.
    """
    responses = []
    for messages in trajectories:
        parsed = parse_openai_agents_trajectory(messages)
        # Extract final answer: last assistant message with string content
        final_answer = None
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and isinstance(msg.get("content"), str) and msg["content"].strip():
                final_answer = msg["content"]
                break

        if final_answer:
            responses.append(
                TrajectoryResponse(
                    task_summary=parsed["task_instruction"],
                    final_answer=final_answer,
                )
            )
    return responses


def generate_output_formatter_policies(
    trajectories: list[list[dict]],
    evaluation_feedback: list[str] | None = None,
) -> list[PolicySuggestion]:
    """
    Analyze trajectory responses and generate OutputFormatter policy suggestions.

    This function:
    1. Extracts final answers from each trajectory
    2. Renders the generate_output_formatter.jinja2 prompt with the response data
    3. Calls LiteLLM to analyze patterns and produce structured policy suggestions
    4. Returns validated PolicySuggestion objects

    Args:
        trajectories: List of raw trajectory message lists. Each trajectory is
            a list of messages as returned by OpenAI Agents SDK.
        evaluation_feedback: Optional list of formatting-related evaluation
            feedback strings (e.g., "Response should use markdown tables").

    Returns:
        List of PolicySuggestion objects for OutputFormatter policies.
    """
    responses = extract_responses_from_trajectories(trajectories)
    if not responses:
        return []

    return _generate_from_responses(responses, evaluation_feedback)


def generate_output_formatter_policies_from_responses(
    responses: list[TrajectoryResponse],
    evaluation_feedback: list[str] | None = None,
) -> list[PolicySuggestion]:
    """
    Generate OutputFormatter policy suggestions from pre-extracted responses.

    Use this when you already have TrajectoryResponse objects (e.g., from
    a demo or when responses are extracted via a different pipeline).

    Args:
        responses: List of TrajectoryResponse objects.
        evaluation_feedback: Optional formatting-related feedback.

    Returns:
        List of PolicySuggestion objects for OutputFormatter policies.
    """
    if not responses:
        return []

    return _generate_from_responses(responses, evaluation_feedback)


def _generate_from_responses(
    responses: list[TrajectoryResponse],
    evaluation_feedback: list[str] | None = None,
) -> list[PolicySuggestion]:
    """Core generation logic shared by both entry points."""
    prompt_file = Path(__file__).parent / "prompts/generate_output_formatter.jinja2"
    supported_params = get_supported_openai_params(
        model=llm_settings.tips_model,
        custom_llm_provider=llm_settings.custom_llm_provider,
    )
    supports_response_format = supported_params and "response_format" in supported_params
    response_schema_enabled = supports_response_schema(
        model=llm_settings.tips_model,
        custom_llm_provider=llm_settings.custom_llm_provider,
    )
    constrained_decoding_supported = supports_response_format and response_schema_enabled

    prompt = Template(prompt_file.read_text()).render(
        num_responses=len(responses),
        responses=[{"task_summary": r.task_summary, "final_answer": r.final_answer} for r in responses],
        evaluation_feedback=evaluation_feedback,
        constrained_decoding_supported=constrained_decoding_supported,
    )

    if constrained_decoding_supported:
        litellm.enable_json_schema_validation = True
        clean_response = (
            completion(
                model=llm_settings.tips_model,
                messages=[{"role": "user", "content": prompt}],
                response_format=PolicyGenerationResponse,
                custom_llm_provider=llm_settings.custom_llm_provider,
            )
            .choices[0]
            .message.content
        )
    else:
        litellm.enable_json_schema_validation = False
        response = (
            completion(
                model=llm_settings.tips_model,
                messages=[{"role": "user", "content": prompt}],
                custom_llm_provider=llm_settings.custom_llm_provider,
            )
            .choices[0]
            .message.content
        )
        clean_response = clean_llm_response(response)

    return PolicyGenerationResponse.model_validate(json.loads(clean_response)).suggestions
