"""
Shared HTTP helpers with SAFE path fallback.

Why this exists
---------------
The two base URLs (ROBERTO_API_BASE and ROBERTO_API_BASE_PUBLIC) have caused
confusion about whether routes live under `/api/...`, `/api/v1/...`, or
`/api/v1/public/...`. Earlier probing showed some documented paths returned 404
because the prefix didn't match what's deployed.

To stay robust regardless of the exact base values, these helpers try a list of
candidate URLs in order. But for write operations (POST that creates leads /
bookings / sends a message) we must NOT blindly retry, or we could create
DUPLICATES. So the rule is:

  - Move on to the next candidate ONLY when the route clearly doesn't exist
    (HTTP 404) or the request never reached the server (connection/timeout
    error). In those cases nothing was created, so trying the next path is safe.
  - As soon as a candidate returns ANYTHING else (2xx success, or 4xx/5xx like
    400/401/422/500), STOP — that route exists and handled the request. Retrying
    would risk a duplicate or hide a real error.

Each candidate is built from the configured bases, so if an env value already
contains `/v1`, the de-duplication below prevents a double `/v1/v1`.
"""

import httpx


def _norm(base: str) -> str:
    return (base or "").rstrip("/")


def build_candidates(bases: list, suffixes: list) -> list:
    """
    Build a de-duplicated, ordered list of candidate URLs from every
    (base, suffix) combination. Collapses accidental `/v1/v1` and `/public/public`.
    """
    seen = set()
    out = []
    for base in bases:
        b = _norm(base)
        if not b:
            continue
        for suf in suffixes:
            url = b + suf
            # Collapse accidental duplicate segments from base+suffix overlap.
            url = url.replace("/v1/v1/", "/v1/").replace("/public/public/", "/public/")
            if url not in seen:
                seen.add(url)
                out.append(url)
    return out


async def post_with_fallback(candidates: list, json: dict, headers: dict,
                             timeout: float = 10.0, log_tag: str = "HTTP"):
    """
    POST to each candidate in order. Stop on the first one that the server
    actually handles. Only fall through on 404 or transport-level errors.

    Returns the httpx.Response of the handling route, or None if every candidate
    was a 404 / unreachable.
    """
    last_resp = None
    async with httpx.AsyncClient() as client:
        for url in candidates:
            try:
                resp = await client.post(url, json=json, headers=headers, timeout=timeout)
                print(f"[{log_tag}] POST {url} -> {resp.status_code}")
                if resp.status_code == 404:
                    # Route not found here — safe to try the next candidate.
                    last_resp = resp
                    continue
                # Any other status means this route handled it (success or a real
                # error). Do NOT retry elsewhere — that could duplicate data.
                return resp
            except Exception as e:
                # Never reached the server — safe to try the next candidate.
                print(f"[{log_tag}] POST {url} failed transport: "
                      f"{type(e).__name__}: {e}")
                continue
    return last_resp


async def get_with_fallback(candidates: list, headers: dict,
                            timeout: float = 10.0, log_tag: str = "HTTP"):
    """
    GET variant. GETs are read-only and idempotent, so retrying is always safe;
    we still stop at the first non-404 response.
    Returns the handling response, or None if all were 404 / unreachable.
    """
    last_resp = None
    async with httpx.AsyncClient() as client:
        for url in candidates:
            try:
                resp = await client.get(url, headers=headers, timeout=timeout)
                print(f"[{log_tag}] GET {url} -> {resp.status_code}")
                if resp.status_code == 404:
                    last_resp = resp
                    continue
                return resp
            except Exception as e:
                print(f"[{log_tag}] GET {url} failed transport: "
                      f"{type(e).__name__}: {e}")
                continue
    return last_resp