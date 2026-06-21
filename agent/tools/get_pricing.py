import httpx
from langchain_core.tools import tool
from core.config import ROBERTO_API_BASE, ROBERTO_API_BASE_PUBLIC, ROBERTO_API_TOKEN
from agent.tools.http_fallback import build_candidates, get_with_fallback


def _pricing_candidates(branch_id: str):
    # Documented: {base}/public/pricings/{branchId} where base already has /v1.
    # We try several prefixes so it works regardless of how the bases are set.
    return build_candidates(
        bases=[ROBERTO_API_BASE_PUBLIC, ROBERTO_API_BASE],
        suffixes=[
            f"/public/pricings/{branch_id}",
            f"/v1/public/pricings/{branch_id}",
            f"/pricings/{branch_id}",
        ],
    )


def make_get_pricing(business_id: str, branch_id: str = None):

    @tool
    async def get_pricing_rule() -> str:
        """
        ALWAYS call this tool FIRST whenever the customer asks about price, cost,
        rate, or shipping charges for a PARCEL/CARGO shipment - before using
        search_knowledge.

        Fetches the official pricing rule configured by the business admin.
        The structure of the pricing data may vary - it could contain fields like
        baseFare, perKgFare, perKmFare, freeWeightLimitKg, totalFee,
        installmentDetails, or other fields not listed here. Read whatever fields
        are present and use your judgement to calculate the price, asking the
        customer for any missing information you need (like weight or distance).

        If no rule is found (empty result), fall back to search_knowledge to find
        the rate from the knowledge base instead.
        """
        if not branch_id:
            return "NO_PRICING_RULE_FOUND"

        try:
            resp = await get_with_fallback(
                candidates=_pricing_candidates(branch_id),
                headers={
                    "x-api-token": ROBERTO_API_TOKEN,
                    "Content-Type": "application/json",
                },
                log_tag="PRICING",
            )

            if resp is None or resp.status_code != 200:
                return "NO_PRICING_RULE_FOUND"

            print(f"[PRICING] Response: {resp.text[:500]}")
            payload = resp.json()
            rules = payload.get("data", [])

            if not rules:
                return "NO_PRICING_RULE_FOUND"

            active_rules = [r for r in rules if r.get("status") is True]
            rule = active_rules[0] if active_rules else rules[0]

            # Pass the raw rule through as-is - structure may vary.
            # The LLM reads whatever fields exist and reasons about them.
            return (
                f"PRICING_RULE_FOUND\n"
                f"Raw pricing data (structure may vary, read carefully): {rule}\n"
                f"Instructions: Examine the 'type' and 'configuration' fields above. "
                f"Use whatever numeric fields are present (e.g. baseFare, perKgFare, "
                f"totalFee, installmentDetails, or any other field) to calculate or "
                f"explain the price. Ask the customer for any input you still need "
                f"(such as weight or distance) before finalizing the calculation."
            )

        except Exception as e:
            print(f"[PRICING ERROR] {e}")
            return "NO_PRICING_RULE_FOUND"

    return get_pricing_rule