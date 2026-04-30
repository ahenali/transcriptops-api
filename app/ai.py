import json
import os
import logging
from openai import AsyncOpenAI
from fastapi import HTTPException, status

from app.prompts import (
    EXTRACT_SYSTEM, EXTRACT_USER,
    SUMMARIZE_SYSTEM, SUMMARIZE_USER,
    DEAL_SIGNALS_SYSTEM, DEAL_SIGNALS_USER,
)

logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"  # fast + cheap; swap to gpt-4o for higher accuracy


def _get_client() -> AsyncOpenAI:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    return AsyncOpenAI(api_key=key)


async def _chat(system: str, user: str, temperature: float = 0.2) -> dict:
    """
    Core OpenAI chat call. Returns parsed JSON dict.
    temperature=0.2 keeps outputs consistent across runs.
    """
    client = _get_client()
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        )
    except Exception as exc:
        logger.error("OpenAI API error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "AI service unavailable. Please retry in a moment.", "detail": str(exc)},
        )

    raw = response.choices[0].message.content or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("JSON parse failure. Raw output: %s", raw)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Malformed AI response. Our team has been notified.", "detail": str(exc)},
        )


async def extract_transcript(transcript: str, language: str) -> dict:
    user_msg = EXTRACT_USER.format(language=language, transcript=transcript)
    return await _chat(EXTRACT_SYSTEM, user_msg)


async def summarize_transcript(transcript: str, bullet_count: int) -> dict:
    user_msg = SUMMARIZE_USER.format(bullet_count=bullet_count, transcript=transcript)
    return await _chat(SUMMARIZE_SYSTEM, user_msg)


async def extract_deal_signals(transcript: str) -> dict:
    user_msg = DEAL_SIGNALS_USER.format(transcript=transcript)
    return await _chat(DEAL_SIGNALS_SYSTEM, user_msg)
