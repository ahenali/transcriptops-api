import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

# RapidAPI injects this header automatically on every request.
# When testing directly (not via RapidAPI), callers pass X-API-Key instead.
RAPIDAPI_PROXY_SECRET = APIKeyHeader(name="X-RapidAPI-Proxy-Secret", auto_error=False)
DIRECT_API_KEY        = APIKeyHeader(name="X-API-Key", auto_error=False)


def _load_valid_keys() -> set[str]:
    """Load allowed API keys from the environment variable (comma-separated)."""
    raw = os.getenv("VALID_API_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}


async def require_api_key(
    rapid_secret: str | None = Security(RAPIDAPI_PROXY_SECRET),
    direct_key:   str | None = Security(DIRECT_API_KEY),
) -> str:
    """
    Two-path authentication:

    Path A — RapidAPI traffic
        RapidAPI injects X-RapidAPI-Proxy-Secret on every forwarded request.
        We verify it matches the secret shown in the RapidAPI provider dashboard.

    Path B — Direct / testing traffic
        Caller passes X-API-Key with a key from your VALID_API_KEYS env var.
        Use this for your own testing and for early customers before RapidAPI.

    Returns the verified key string so you can use it for per-key logging.
    """

    # Path A: RapidAPI proxy secret
    rapidapi_secret_env = os.getenv("RAPIDAPI_PROXY_SECRET", "")
    if rapid_secret and rapidapi_secret_env and rapid_secret == rapidapi_secret_env:
        return rapid_secret

    # Path B: direct API key
    valid_keys = _load_valid_keys()
    if direct_key and direct_key in valid_keys:
        return direct_key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": "Invalid or missing API key.",
            "hint": "Pass your key in the X-API-Key header. "
                    "Get a key at https://rapidapi.com/your-username/api/transcriptops",
        },
    )
