# auth/api_key.py
# Step 0: API key validation + domain lock logic.
# Per SRS §3.4 (Option A) — keys stored in env vars, loaded into memory at startup.
# Security gate: both key validity AND origin domain must pass before any image processing.

import os
from fastapi import Header, HTTPException, Request
from functools import lru_cache


# ── In-memory store (loaded once at startup) ─────────────────────────────────

def _build_key_store() -> dict[str, str]:
    """
    Parse VALID_API_KEYS and API_KEY_DOMAINS env vars into a dict:
        { "key1": "store1.com", "key2": "store2.in", ... }

    Env var formats (from SRS §3.4):
        VALID_API_KEYS=key1,key2,key3
        API_KEY_DOMAINS=key1:store1.com,key2:store2.in
    """
    raw_keys = os.getenv("VALID_API_KEYS", "")
    raw_domains = os.getenv("API_KEY_DOMAINS", "")

    valid_keys: set[str] = {k.strip() for k in raw_keys.split(",") if k.strip()}
    domain_map: dict[str, str] = {}

    for entry in raw_domains.split(","):
        entry = entry.strip()
        if ":" in entry:
            key, domain = entry.split(":", 1)
            domain_map[key.strip()] = domain.strip().lower()

    # Build final store — only include keys that appear in both vars
    store: dict[str, str] = {}
    for key in valid_keys:
        store[key] = domain_map.get(key, "*")  # "*" means no domain restriction
    return store


# Load once at module import time (app startup)
_KEY_STORE: dict[str, str] = _build_key_store()


# ── Origin extraction helper ──────────────────────────────────────────────────

def _extract_origin_host(origin: str | None, referer: str | None) -> str:
    """
    Extract the bare hostname from an Origin or Referer header.
    Returns empty string if neither is present.
    """
    raw = origin or referer or ""
    # Strip scheme: https://store.com/path → store.com/path → store.com
    for prefix in ("https://", "http://"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
            break
    return raw.split("/")[0].split(":")[0].lower()


# ── FastAPI dependency ────────────────────────────────────────────────────────

async def get_api_key(
    request: Request,
    authorization: str | None = Header(default=None),
) -> str:
    """
    FastAPI Depends() dependency.
    Validates API key AND origin domain. Raises HTTP 401 on any failure.
    Returns the validated api_key string on success.
    """
    # 1. Extract Bearer token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"error_code": "MISSING_API_KEY", "message": "Authorization header with Bearer token is required."},
        )
    api_key = authorization[len("Bearer "):]

    # 2. Check key exists
    if api_key not in _KEY_STORE:
        raise HTTPException(
            status_code=401,
            detail={"error_code": "INVALID_API_KEY", "message": "The provided API key is not recognized."},
        )

    # 3. Check domain lock
    registered_domain = _KEY_STORE[api_key]
    if registered_domain != "*":
        request_host = _extract_origin_host(
            request.headers.get("origin"),
            request.headers.get("referer"),
        )
        if request_host != registered_domain:
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "DOMAIN_MISMATCH",
                    "message": f"This API key is not authorized for origin '{request_host}'.",
                },
            )

    return api_key
