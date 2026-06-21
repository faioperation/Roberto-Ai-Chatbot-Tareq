from typing import TypedDict, Optional

# LangGraph state — carries all data through the agent graph
class AgentState(TypedDict):
    business_id: str
    training_data_id: Optional[str]
    subject: str
    recipient_id: str
    channel: str
    message: str
    conversation_id: Optional[str]
    business_profile: Optional[dict]
    training_data: Optional[list]
    context: Optional[str]
    response: Optional[str]