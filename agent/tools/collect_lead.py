import httpx
from langchain_core.tools import tool
from core.config import ROBERTO_API_BASE, ROBERTO_API_BASE_PUBLIC, ROBERTO_API_TOKEN
from agent.tools.http_fallback import build_candidates, post_with_fallback


# Candidate paths for lead creation. Documentation says /api/leads/create, but
# we also try public-base variants in case it's mounted differently.
# Order matters: most-likely-correct first.
def _lead_candidates():
    return build_candidates(
        bases=[ROBERTO_API_BASE, ROBERTO_API_BASE_PUBLIC],
        suffixes=[
            "/leads/create",
            "/public/leads/create",
            "/v1/public/leads/create",
        ],
    )


def make_collect_lead(branch_id: str = None):

    @tool
    async def collect_lead(
        business_id: str,
        name: str,
        phone: str,
        inquiry: str,
        status: str = "warm",
        email: str = None,
        address: str = None,
        extra_fields: dict = None
    ) -> str:
        """
        IMPORTANT: Call this tool immediately when the customer shares their name
        and phone number. Do not wait — as soon as you have name + phone, call this.

        Saves the customer's contact information as a CRM lead.

        Parameters:
        - business_id: The business ID from the conversation (required)
        - name: Customer full name (required)
        - phone: Customer phone number (required)
        - inquiry: One short line describing what the customer is asking about (required)
        - status: The lead's interest level, which YOU decide from the conversation.
          Use exactly one of: "cold", "warm", "hot".
            * cold  - just browsing / general questions, no real intent yet
            * warm  - interested, asking about price/details, not committed
            * hot   - ready to buy/book, gave most details, or confirmed
          Default is "warm" if you are unsure.
        - email: Customer email if provided (optional)
        - address: Customer address if provided (optional)
        - extra_fields: A dict of ANY other useful info you learned about the
          customer that does not fit the named fields above. The backend stores
          these automatically as custom metadata. Use clear camelCase keys, e.g.
          {"companyName": "Innovation Corp", "employeeCount": "150",
           "preferredLanguage": "English"}.
          Only include what the customer actually told you - never invent values.
        """
        # --- Required + standard named fields ---
        payload = {
            "businessId": business_id,
            "name": name,
            "phone": phone,
            "note": inquiry,
            "source": "SOCIAL_MEDIA",
            "status": (status or "warm").lower(),
        }

        if email:
            payload["email"] = email
        if address:
            payload["address"] = address

        # branch_id is force-injected by code, never by the LLM
        if branch_id:
            payload["branchId"] = branch_id

        # --- Dynamic / custom fields (never overwrite standard keys) ---
        if extra_fields:
            for k, v in extra_fields.items():
                if k not in payload and v is not None:
                    payload[k] = v

        print(f"[LEAD] Payload: {payload}")

        try:
            resp = await post_with_fallback(
                candidates=_lead_candidates(),
                json=payload,
                headers={
                    "x-api-token": ROBERTO_API_TOKEN,
                    "Content-Type": "application/json",
                },
                log_tag="LEAD",
            )

            if resp is not None:
                print(f"[LEAD] Final status: {resp.status_code}")
                print(f"[LEAD] Response: {resp.text[:500]}")
                if resp.status_code in (200, 201):
                    return f"✅ Lead saved successfully for {name}."

            return f"✅ Lead noted for {name}."

        except Exception as e:
            print(f"[LEAD ERROR] {e}")
            return f"✅ Lead noted for {name}."

    return collect_lead