from langchain_core.tools import tool

@tool
def calculate_price(
    destination: str,
    weight: float,
    base_fare: float = 0,
    rate_per_kg: float = 0,
    free_weight_limit_kg: float = 0
) -> str:
    """
    Calculate shipping price based on destination and weight.
    Always adds 75 QAR customs fee for cargo shipments.

    Usage:
    - If get_pricing_rule returned PRICING_RULE_FOUND, use its baseFare,
      perKgFare, and freeWeightLimitKg values here.
    - If get_pricing_rule returned NO_PRICING_RULE_FOUND, use search_knowledge
      to find rate_per_kg instead, and leave base_fare and free_weight_limit_kg as 0.
    """
    CUSTOMS_FEE = 75

    billable_weight = max(0, weight - free_weight_limit_kg)
    cargo_cost = base_fare + (rate_per_kg * billable_weight)
    total = cargo_cost + CUSTOMS_FEE

    return (
        f"Shipping estimate to {destination}:\n"
        f"- Base fare: {base_fare} QAR\n"
        f"- Rate: {rate_per_kg} QAR/kg\n"
        f"- Billable weight: {billable_weight} kg (free limit: {free_weight_limit_kg} kg)\n"
        f"- Cargo cost: {cargo_cost} QAR\n"
        f"- Customs fee: {CUSTOMS_FEE} QAR\n"
        f"- Total: {total} QAR\n"
        f"- Pickup: FREE inside Qatar"
    )