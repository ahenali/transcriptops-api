from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


# ── /transcript/extract ──────────────────────────────────────────────────────

class ExtractRequest(BaseModel):
    transcript: str = Field(
        ...,
        min_length=50,
        max_length=50_000,
        description="Raw transcript text. Min 50 chars, max 50,000.",
        examples=["John: Let's sync on the Q3 timeline. Sarah: Sure, I'll send the report by Friday..."],
    )
    language: Optional[str] = Field(
        default="en",
        description="ISO 639-1 language code of the transcript.",
    )


class ActionItem(BaseModel):
    task: str
    owner: Optional[str] = None
    due: Optional[str] = None


class ExtractResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    action_items: list[ActionItem]
    summary: str
    sentiment: str = Field(description="overall | positive | neutral | negative | mixed")
    key_topics: list[str]
    word_count: int
    model_used: str


# ── /transcript/summarize ────────────────────────────────────────────────────

class SummarizeRequest(BaseModel):
    transcript: str = Field(
        ...,
        min_length=50,
        max_length=50_000,
        description="Raw transcript text to summarize.",
    )
    bullet_count: Optional[int] = Field(
        default=5,
        ge=3,
        le=10,
        description="Number of bullet points in the summary (3–10).",
    )


class SummarizeResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    bullets: list[str]
    one_liner: str = Field(description="Single sentence TL;DR of the entire meeting.")
    duration_estimate: str = Field(description="Estimated meeting length based on content.")
    model_used: str


# ── /deal/signals ─────────────────────────────────────────────────────────────

class DealSignalsRequest(BaseModel):
    transcript: str = Field(
        ...,
        min_length=50,
        max_length=50_000,
        description="Sales call or meeting transcript.",
    )


class DealSignalsResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    budget_mentioned: Optional[str] = Field(
        description="Budget figure or range mentioned, or null if not discussed."
    )
    timeline: Optional[str] = Field(
        description="Decision or purchase timeline mentioned by the prospect."
    )
    decision_maker: Optional[str] = Field(
        description="Name or role of the final decision maker identified."
    )
    deal_stage: str = Field(
        description="awareness | interest | evaluation | decision | closed_won | closed_lost"
    )
    objections: list[str] = Field(description="List of objections raised by the prospect.")
    next_steps: list[str] = Field(description="Agreed next steps from the conversation.")
    deal_score: int = Field(
        description="Deal health score 0–100. Higher = more likely to close.", ge=0, le=100
    )
    model_used: str


# ── Shared error response ─────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    docs: str = "https://rapidapi.com/your-username/api/transcriptops"


# ── /transcript/extract ──────────────────────────────────────────────────────

class ExtractRequest(BaseModel):
    transcript: str = Field(
        ...,
        min_length=50,
        max_length=50_000,
        description="Raw transcript text. Min 50 chars, max 50,000.",
        examples=["John: Let's sync on the Q3 timeline. Sarah: Sure, I'll send the report by Friday..."],
    )
    language: Optional[str] = Field(
        default="en",
        description="ISO 639-1 language code of the transcript.",
    )


class ActionItem(BaseModel):
    task: str
    owner: Optional[str] = None
    due: Optional[str] = None


class ExtractResponse(BaseModel):
    action_items: list[ActionItem]
    summary: str
    sentiment: str = Field(description="overall | positive | neutral | negative | mixed")
    key_topics: list[str]
    word_count: int
    model_used: str


# ── /transcript/summarize ────────────────────────────────────────────────────

class SummarizeRequest(BaseModel):
    transcript: str = Field(
        ...,
        min_length=50,
        max_length=50_000,
        description="Raw transcript text to summarize.",
    )
    bullet_count: Optional[int] = Field(
        default=5,
        ge=3,
        le=10,
        description="Number of bullet points in the summary (3–10).",
    )


class SummarizeResponse(BaseModel):
    bullets: list[str]
    one_liner: str = Field(description="Single sentence TL;DR of the entire meeting.")
    duration_estimate: str = Field(description="Estimated meeting length based on content.")
    model_used: str


# ── /deal/signals ─────────────────────────────────────────────────────────────

class DealSignalsRequest(BaseModel):
    transcript: str = Field(
        ...,
        min_length=50,
        max_length=50_000,
        description="Sales call or meeting transcript.",
    )


class DealSignalsResponse(BaseModel):
    budget_mentioned: Optional[str] = Field(
        description="Budget figure or range mentioned, or null if not discussed."
    )
    timeline: Optional[str] = Field(
        description="Decision or purchase timeline mentioned by the prospect."
    )
    decision_maker: Optional[str] = Field(
        description="Name or role of the final decision maker identified."
    )
    deal_stage: str = Field(
        description="awareness | interest | evaluation | decision | closed_won | closed_lost"
    )
    objections: list[str] = Field(description="List of objections raised by the prospect.")
    next_steps: list[str] = Field(description="Agreed next steps from the conversation.")
    deal_score: int = Field(
        description="Deal health score 0–100. Higher = more likely to close.", ge=0, le=100
    )
    model_used: str


# ── Shared error response ─────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    docs: str = "https://rapidapi.com/your-username/api/transcriptops"
