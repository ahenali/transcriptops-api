"""
Run with: pytest tests/ -v
These tests mock the OpenAI call so you don't burn tokens during CI.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

import os
os.environ["VALID_API_KEYS"] = "test_key_abc"
os.environ["OPENAI_API_KEY"] = "sk-fake"
os.environ["RATE_LIMIT_PER_MINUTE"] = "1000"

from app.main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "test_key_abc"}


FAKE_EXTRACT = {
    "action_items": [
        {"task": "Send Q3 report", "owner": "Sarah", "due": "Friday"},
        {"task": "Schedule follow-up call", "owner": "John", "due": None},
    ],
    "summary": "The team discussed Q3 targets and upcoming deliverables.",
    "sentiment": "positive",
    "key_topics": ["Q3 targets", "deliverables", "follow-up"],
}

FAKE_SUMMARIZE = {
    "bullets": [
        "Team agreed on a Friday deadline for the Q3 report.",
        "John will schedule a follow-up call for next week.",
        "Budget constraints were flagged as a risk.",
    ],
    "one_liner": "Q3 planning meeting with clear deadlines and next steps agreed.",
    "duration_estimate": "~30 minutes",
}

FAKE_DEAL = {
    "budget_mentioned": "$50,000",
    "timeline": "end of Q3",
    "decision_maker": "CFO",
    "deal_stage": "evaluation",
    "objections": ["Price is above current budget", "Need board approval"],
    "next_steps": ["Send pricing deck", "Schedule CFO intro call"],
    "deal_score": 62,
}

SAMPLE_TRANSCRIPT = (
    "John: Hey Sarah, let's talk about the Q3 numbers. "
    "Sarah: Sure. We need the report done by Friday. I'll handle the analysis. "
    "John: Great. Also, can you schedule a follow-up call? "
    "Sarah: Will do. I'm feeling good about where we're landing. "
    "John: Same here. Let's keep the momentum going."
)


# ── Health ────────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_missing_api_key():
    r = client.post("/transcript/extract", json={"transcript": SAMPLE_TRANSCRIPT})
    assert r.status_code == 401


def test_invalid_api_key():
    r = client.post(
        "/transcript/extract",
        headers={"X-API-Key": "wrong_key"},
        json={"transcript": SAMPLE_TRANSCRIPT},
    )
    assert r.status_code == 401


# ── /transcript/extract ───────────────────────────────────────────────────────

@patch("app.main.extract_transcript", new_callable=AsyncMock, return_value=FAKE_EXTRACT)
def test_extract_success(mock_ai):
    r = client.post(
        "/transcript/extract",
        headers=HEADERS,
        json={"transcript": SAMPLE_TRANSCRIPT, "language": "en"},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["action_items"]) == 2
    assert data["action_items"][0]["task"] == "Send Q3 report"
    assert data["action_items"][0]["owner"] == "Sarah"
    assert data["sentiment"] == "positive"
    assert data["model_used"] == "gpt-4o-mini"


def test_extract_transcript_too_short():
    r = client.post(
        "/transcript/extract",
        headers=HEADERS,
        json={"transcript": "Too short."},
    )
    assert r.status_code == 422


# ── /transcript/summarize ─────────────────────────────────────────────────────

@patch("app.main.summarize_transcript", new_callable=AsyncMock, return_value=FAKE_SUMMARIZE)
def test_summarize_success(mock_ai):
    r = client.post(
        "/transcript/summarize",
        headers=HEADERS,
        json={"transcript": SAMPLE_TRANSCRIPT, "bullet_count": 3},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["bullets"]) == 3
    assert "one_liner" in data
    assert data["model_used"] == "gpt-4o-mini"


def test_summarize_bullet_count_out_of_range():
    r = client.post(
        "/transcript/summarize",
        headers=HEADERS,
        json={"transcript": SAMPLE_TRANSCRIPT, "bullet_count": 15},
    )
    assert r.status_code == 422


# ── /deal/signals ─────────────────────────────────────────────────────────────

@patch("app.main.extract_deal_signals", new_callable=AsyncMock, return_value=FAKE_DEAL)
def test_deal_signals_success(mock_ai):
    r = client.post(
        "/deal/signals",
        headers=HEADERS,
        json={"transcript": SAMPLE_TRANSCRIPT},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["budget_mentioned"] == "$50,000"
    assert data["deal_stage"] == "evaluation"
    assert 0 <= data["deal_score"] <= 100
    assert isinstance(data["objections"], list)
    assert isinstance(data["next_steps"], list)


@patch("app.main.extract_deal_signals", new_callable=AsyncMock, return_value={**FAKE_DEAL, "deal_score": 150})
def test_deal_score_clamped(mock_ai):
    r = client.post(
        "/deal/signals",
        headers=HEADERS,
        json={"transcript": SAMPLE_TRANSCRIPT},
    )
    assert r.status_code == 200
    assert r.json()["deal_score"] == 100
