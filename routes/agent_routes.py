from fastapi import APIRouter, Depends
from core.security import verify_token
from webhooks.incoming import handle_incoming, paused_conversations

router = APIRouter()

# Main message endpoint — Roberto sends messages here
@router.post("/agent/message")
async def agent_message(payload: dict, _=Depends(verify_token)):
    business_id = payload.get("business_id")
    recipient_id = payload.get("recipient_id")

    # Check if AI is paused for this conversation
    key = f"{business_id}:{recipient_id}"
    if key in paused_conversations:
        return {"status": "ok", "paused": True, "response": None}

    # Process message and get AI response
    response = await handle_incoming(payload)
    return {"status": "ok", "paused": False, "response": response}

# Handoff control endpoint — Roberto calls this to pause or resume AI
@router.post("/agent/handoff")
async def agent_handoff(payload: dict, _=Depends(verify_token)):
    business_id = payload.get("business_id")
    recipient_id = payload.get("recipient_id")
    action = payload.get("action")  # "pause" or "resume"

    key = f"{business_id}:{recipient_id}"

    if action == "pause":
        paused_conversations.add(key)
        return {"status": "paused"}

    elif action == "resume":
        paused_conversations.discard(key)
        return {"status": "resumed"}

    return {"status": "error", "message": "action must be pause or resume"}