import os
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

from app.auth import require_api_key
from app.models import (
    ExtractRequest, ExtractResponse,
    SummarizeRequest, SummarizeResponse,
    DealSignalsRequest, DealSignalsResponse,
    ActionItem,
)
from app.ai import extract_transcript, summarize_transcript, extract_deal_signals

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)

# ── Rate limiter ──────────────────────────────────────────────────────────────
# Uses the caller's IP by default. On RapidAPI, swap get_remote_address for a
# function that reads the X-RapidAPI-User header to rate-limit per user account.

rpm = os.getenv("RATE_LIMIT_PER_MINUTE", "20")
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{rpm}/minute"])


# ── App lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("TranscriptOps API starting up — version %s", os.getenv("APP_VERSION", "1.0.0"))
    yield
    logger.info("TranscriptOps API shutting down.")


# ── App init ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="TranscriptOps API",
    description=(
        "Extract action items, deal signals, and executive summaries from any "
        "meeting or call transcript. Built for Make, n8n, and CRM workflows."
    ),
    version=os.getenv("APP_VERSION", "1.0.0"),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Request timing middleware ─────────────────────────────────────────────────

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    ms = round((time.perf_counter() - start) * 1000, 1)
    response.headers["X-Process-Time-Ms"] = str(ms)
    return response


# ── Global error handler ──────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error.", "detail": str(exc)},
    )


# ── Health check (RapidAPI requires this) ─────────────────────────────────────

@app.get(
    "/health",
    tags=["Status"],
    summary="Health check",
    response_description="API status and version",
)
async def health():
    return {
        "status": "ok",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "model": "gpt-4o-mini",
    }


# ── POST /transcript/extract ──────────────────────────────────────────────────

@app.post(
    "/transcript/extract",
    response_model=ExtractResponse,
    tags=["Transcript"],
    summary="Extract action items, sentiment & topics",
    responses={
        401: {"description": "Invalid or missing API key"},
        422: {"description": "Validation error — check your request body"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "AI service temporarily unavailable"},
    },
)
@limiter.limit(f"{rpm}/minute")
async def extract(
    request: Request,
    body: ExtractRequest,
    api_key: str = Depends(require_api_key),
):
    """
    Parse any meeting or call transcript and return:

    - **action_items** — tasks with owner and due date
    - **summary** — 2–3 sentence plain-English recap
    - **sentiment** — overall tone of the meeting
    - **key_topics** — 3–6 main subjects discussed

    **Max input:** 50,000 characters (~6,000 words / ~60 min meeting).
    """
    logger.info("extract called | key=...%s | chars=%d", api_key[-6:], len(body.transcript))

    data = await extract_transcript(body.transcript, body.language or "en")

    raw_items = data.get("action_items", [])
    action_items = [
        ActionItem(
            task=item.get("task", ""),
            owner=item.get("owner"),
            due=item.get("due"),
        )
        for item in raw_items
        if item.get("task")
    ]

    return ExtractResponse(
        action_items=action_items,
        summary=data.get("summary", ""),
        sentiment=data.get("sentiment", "neutral"),
        key_topics=data.get("key_topics", []),
        word_count=len(body.transcript.split()),
        model_used="gpt-4o-mini",
    )


# ── POST /transcript/summarize ────────────────────────────────────────────────

@app.post(
    "/transcript/summarize",
    response_model=SummarizeResponse,
    tags=["Transcript"],
    summary="Generate a bullet-point executive summary",
    responses={
        401: {"description": "Invalid or missing API key"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "AI service temporarily unavailable"},
    },
)
@limiter.limit(f"{rpm}/minute")
async def summarize(
    request: Request,
    body: SummarizeRequest,
    api_key: str = Depends(require_api_key),
):
    """
    Turn a raw transcript into an executive-ready summary:

    - **bullets** — N concise bullet points (default 5, configurable 3–10)
    - **one_liner** — single sentence TL;DR
    - **duration_estimate** — estimated meeting length based on content

    Ideal for piping into Slack notifications, email digests, or CRM notes.
    """
    logger.info("summarize called | key=...%s | bullets=%d", api_key[-6:], body.bullet_count or 5)

    data = await summarize_transcript(body.transcript, body.bullet_count or 5)

    return SummarizeResponse(
        bullets=data.get("bullets", []),
        one_liner=data.get("one_liner", ""),
        duration_estimate=data.get("duration_estimate", "unknown"),
        model_used="gpt-4o-mini",
    )


# ── POST /deal/signals ────────────────────────────────────────────────────────

@app.post(
    "/deal/signals",
    response_model=DealSignalsResponse,
    tags=["Sales Intelligence"],
    summary="Extract CRM-ready deal signals from a sales call",
    responses={
        401: {"description": "Invalid or missing API key"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "AI service temporarily unavailable"},
    },
)
@limiter.limit(f"{rpm}/minute")
async def deal_signals(
    request: Request,
    body: DealSignalsRequest,
    api_key: str = Depends(require_api_key),
):
    """
    Analyze a B2B sales call transcript and extract:

    - **budget_mentioned** — exact figure or range if stated
    - **timeline** — prospect's decision/purchase timeline
    - **decision_maker** — name or role of final approver
    - **deal_stage** — where this deal sits in the funnel
    - **objections** — concerns raised by the prospect
    - **next_steps** — agreed follow-up actions
    - **deal_score** — 0–100 deal health score

    Push the response body directly to HubSpot or Salesforce custom fields.
    """
    logger.info("deal_signals called | key=...%s | chars=%d", api_key[-6:], len(body.transcript))

    data = await extract_deal_signals(body.transcript)

    score = data.get("deal_score", 0)
    if not isinstance(score, int):
        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 0
    score = max(0, min(100, score))

    return DealSignalsResponse(
        budget_mentioned=data.get("budget_mentioned"),
        timeline=data.get("timeline"),
        decision_maker=data.get("decision_maker"),
        deal_stage=data.get("deal_stage", "awareness"),
        objections=data.get("objections", []),
        next_steps=data.get("next_steps", []),
        deal_score=score,
        model_used="gpt-4o-mini",
    )
