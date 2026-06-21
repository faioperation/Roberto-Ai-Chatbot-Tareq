from langchain_core.tools import tool

@tool
def handoff_human(reason: str) -> str:

    """
    Escalate this conversation to a human agent.
    Use this when:
    - Customer is upset or angry
    - Customer disputes a price
    - Customer needs actual legal advice
    - Issue is too complex for AI to handle
    - Customer requests to speak with a human
    """

    return (
        f"I'm connecting you with a human agent now. "
        f"Please wait a moment. "
        f"Someone from our team will assist you shortly."
    )
    