from agent.agent_runner import run_agent

paused_conversations = set()

async def handle_incoming(payload: dict):
    business_id = payload.get("business_id")
    training_data_id = payload.get("training_data_id")
    subject = payload.get("subject")
    recipient_id = payload.get("recipient_id")
    conversation_id = payload.get("conversation_id")
    channel = payload.get("channel")
    message = payload.get("message")
    branch_id = payload.get("branchId")

    key = f"{business_id}:{recipient_id}"
    if key in paused_conversations:
        print(f"[HANDOFF] AI paused for {key} — human agent handling")
        return None

    response = await run_agent(
        business_id=business_id,
        training_data_id=training_data_id,
        subject=subject,
        recipient_id=recipient_id,
        conversation_id=conversation_id,
        channel=channel,
        message=message,
        branch_id=branch_id
    )
    return response