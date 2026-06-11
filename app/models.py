from __future__ import annotations
from typing import Any, Optional, Literal
from pydantic import BaseModel, Field, model_validator

class TeamsUploadRequest(BaseModel):
    conversation_id: str
    user_id: str
    market: str
    brand: Optional[str] = None
    workshop: str
    language: str = "auto"
    raw_ideas: list[str] = Field(default_factory=list)
    ideas: Optional[list[str]] = None  # accepted for Swagger friendliness

    @model_validator(mode="after")
    def normalize_ideas(self):
        if not self.raw_ideas and self.ideas:
            self.raw_ideas = self.ideas
        return self

class JobEnvelope(BaseModel):
    job_id: str
    conversation_id: str
    user_id: str
    market: str
    brand: Optional[str] = None
    workshop: str
    language: str = "auto"
    raw_ideas: list[str]
    source: str = "teams"
    conversation_reference: Optional[dict[str, Any]] = None

class CleanIdea(BaseModel):
    source_index: int
    raw_text: str
    cleaned_en: str
    market: str
    brand: Optional[str] = None
    component: Optional[str] = None
    sku_range: Optional[str] = None
    action: Optional[str] = None
    language_detected: str = "unknown"
    duplicate_group_id: Optional[str] = None

class RetrievalTrace(BaseModel):
    structured_filters: dict[str, Any]
    market_rule_hits: list[str] = Field(default_factory=list)
    similar_idea_refs: list[str] = Field(default_factory=list)
    material_rows: int = 0
    fallback_used: bool = False

class SavingsBand(BaseModel):
    low_dkk: float
    mid_dkk: float
    high_dkk: float
    method: str
    data_quality: str

class FeasibilityScore(BaseModel):
    score: int
    reason_codes: list[str]
    market_rule_hits: list[str] = Field(default_factory=list)

class OnePager(BaseModel):
    title: str
    summary: str
    implementation_steps: list[str]
    risks: list[str]
    savings_band: SavingsBand
    feasibility: FeasibilityScore
    decision_request: str = "Approve pilot / request SME validation / reject"

class ProcessedIdea(BaseModel):
    idea_id: str
    clean: CleanIdea
    retrieval_trace: RetrievalTrace
    savings_band: SavingsBand
    feasibility: FeasibilityScore
    alternatives: list[str]
    one_pager: OnePager

class AgentResult(BaseModel):
    job_id: str
    conversation_id: str
    market: str
    ideas_processed: int
    duplicates_removed: int
    results: list[ProcessedIdea]
    telemetry: dict[str, Any]

class FeedbackRequest(BaseModel):
    idea_id: str
    conversation_id: str
    market: str
    signal: Literal["accept", "reject", "edit", "needs_sme_review"]
    reason: Optional[str] = None
    corrected_text: Optional[str] = None
    corrected_feasibility: Optional[int] = None

class MarketRuleRequest(BaseModel):
    market: str
    category: str
    constraint: str
    rationale: str
    captured_by: str
    source_conversation_id: str
    valid_from: str
    valid_to: Optional[str] = None
    hardness: Literal["hard_constraint", "soft_resistance", "unknown"] = "unknown"

class ReleaseGateResult(BaseModel):
    gate: str
    value: float | int | str
    threshold: str
    passed: bool
    evidence: str
