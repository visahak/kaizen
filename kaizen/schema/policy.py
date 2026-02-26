from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator


class PolicyType(str, Enum):
    PLAYBOOK = "playbook"
    INTENT_GUARD = "intent_guard"
    TOOL_GUIDE = "tool_guide"
    TOOL_APPROVAL = "tool_approval"
    OUTPUT_FORMATTER = "output_formatter"


class TriggerType(str, Enum):
    KEYWORD = "keyword"
    NATURAL_LANGUAGE = "natural_language"
    ALWAYS = "always"
    # App, State, and Tool triggers can be added here if needed in the future


class PolicyTrigger(BaseModel):
    type: TriggerType
    value: list[str] | None = None
    target: str = "intent"
    operator: str = "or"  # "and" / "or" for keywords
    threshold: float = 0.7  # for natural_language triggers

    @field_validator("value", mode="before")
    @classmethod
    def coerce_value_to_list(cls, v):
        """Coerce a bare string from the LLM into a single-element list."""
        if isinstance(v, str):
            return [v]
        return v


class Policy(BaseModel):
    id: str | None = None
    name: str
    type: PolicyType
    description: str
    triggers: list[PolicyTrigger]
    content: str  # The policy payload (playbook markdown, response text, etc.)
    config: dict[str, Any] = Field(default_factory=dict)  # Type-specific config
    priority: int = 50
    enabled: bool = True


class PolicySuggestion(BaseModel):
    """A single policy suggestion generated from trajectory analysis."""
    name: str = Field(description="Human-readable policy name")
    type: PolicyType = Field(description="The policy type")
    description: str = Field(description="Why this policy is suggested")
    triggers: list[PolicyTrigger] = Field(description="Proposed triggers")
    content: str = Field(description="The policy payload")
    config: dict[str, Any] = Field(default_factory=dict, description="Type-specific config")
    confidence: float = Field(
        description="Confidence score (0.0-1.0) based on pattern strength", ge=0.0, le=1.0
    )
    evidence: str = Field(description="Summary of the trajectory evidence that led to this suggestion")


class PolicyGenerationResponse(BaseModel):
    """LLM response containing generated policy suggestions from trajectories."""
    suggestions: list[PolicySuggestion] = Field(description="Generated policy suggestions")
