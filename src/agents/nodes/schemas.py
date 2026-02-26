from typing import List, Literal

from pydantic import BaseModel, Field

from src.agents.utils.state import TestGenerationPlan, ValidationResult


class ScopeClassification(BaseModel):
    intent: Literal["ALLOW", "BLOCK"]


class IntentResult(BaseModel):
    intent: Literal["mcq_request", "followup", "utility_task", "clarification"]


class PlannerOutput(TestGenerationPlan):
    edit_mode: bool = False
    edit_target: Literal["all", "specific"] = "all"
    edit_indices: List[int] = Field(default_factory=list)
    edit_strategy: Literal["regenerate", "patch"] = "regenerate"


class OptionsOutput(BaseModel):
    options: List[str] = Field(min_length=4, max_length=4)
    correct_answer: Literal["A", "B", "C", "D"]
    explanation: str = ""


class DistractorsOutput(BaseModel):
    distractors: List[str] = Field(default_factory=list)


class ValidatorOutput(ValidationResult):
    pass
