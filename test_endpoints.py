"""
Expanded probe — find the REAL route path.

The first test showed every /public/... path returns 404 "Route Not Found",
so the documented path doesn't match what's registered on the server. This
script:

  1. Tries many path patterns for the Facebook send (once we find the pattern,
     it applies to instagram + whatsapp too).
  2. POSTs to /api/leads/create and /api/bookings/create to check whether the
     /api family of routes exists at all.

KEY IDEA: a 404 means "no such route". ANYTHING ELSE (400, 401, 422, 200...)
means the route EXISTS — we just need to find which path stops 404ing.

    python expanded_probe.py
"""

import asyncio
import httpx
from core.config import ROBERTO_API_BASE, ROBERTO_API_TOKEN

BASE = (ROBERTO_API_BASE or "").rstrip("/")
ROOT = BASE[:-4] if BASE.endswith("/api") else BASE
HEADERS = {"x-api-token": ROBERTO_API_TOKEN, "Content-Type": "application/json"}

FB_PAYLOAD = {
    "businessId": "4431f851-c8e2-4511-9fa0-3cf655492d97",
    "recipientId": "27208449042119808",
    "message": "probe",
}

# Candidate path patterns for the Facebook send route.
FB_PATHS = [
    "/public/facebook/messages/send",
    "/api/public/facebook/messages/send",
    "/api/v1/public/facebook/messages/send",
    "/v1/public/facebook/messages/send",
    "/public/v1/facebook/messages/send",
    "/public/facebook/message/send",        # singular "message"
    "/public/messages/facebook/send",       # order swapped
    "/public/channels/facebook/messages/send",
    "/api/facebook/messages/send",
    "/facebook/messages/send",
    "/public/facebook/send",
    "/api/public/messages/send",
]

LEADS_PAYLOAD = {
    "businessId": "4431f851-c8e2-4511-9fa0-3cf655492d97",
    "name": "Probe Lead",
}
BOOKINGS_PAYLOAD = {
    "businessId": "4431f851-c8e2-4511-9fa0-3cf655492d97",
    "customerName": "Probe",
    "customerNumber": "01900000000",
    "address": "Dhaka",
    "deliveryFromAddress": "Dhaka",
    "productName": "Probe",
    "quantity": 1,
    "size": "Standard",
    "price": 1,
}


def verdict(status: int) -> str:
    if status == 404:
        return "no route here (404)"
    return f"ROUTE EXISTS (status {status}) <-- look here"


async def post(client, url, payload):
    try:
        r = await client.post(url, json=payload, headers=HEADERS, timeout=20.0)
        print(f"  [{r.status_code}] {url}")
        print(f"        {verdict(r.status_code)} | body: {r.text[:160]}")
        return r.status_code
    except Exception as e:
        print(f"  [ERR] {url}  ({type(e).__name__}: {e})")
        return None


async def main():
    print("ROOT =", ROOT, "\n")

    async with httpx.AsyncClient() as client:
        print("### Facebook send — trying path patterns")
        for p in FB_PATHS:
            await post(client, ROOT + p, FB_PAYLOAD)

        print("\n### Does the /api family exist? (leads / bookings)")
        await post(client, f"{ROOT}/api/leads/create", LEADS_PAYLOAD)
        await post(client, f"{ROOT}/api/bookings/create", BOOKINGS_PAYLOAD)

    print("\nAny line that says 'ROUTE EXISTS' is the real path shape.")
    print("If leads/bookings exist but /public sends don't, the send routes")
    print("are mounted somewhere else (or not deployed on this tunnel).")


if __name__ == "__main__":
    asyncio.run(main())