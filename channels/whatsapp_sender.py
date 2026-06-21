from core.config import ROBERTO_API_BASE, ROBERTO_API_BASE_PUBLIC, ROBERTO_API_TOKEN
from agent.tools.http_fallback import build_candidates, post_with_fallback


def _whatsapp_candidates():
    return build_candidates(
        bases=[ROBERTO_API_BASE_PUBLIC, ROBERTO_API_BASE],
        suffixes=[
            "/public/whatsapp/messages/send",
            "/v1/public/whatsapp/messages/send",
            "/whatsapp/messages/send",
        ],
    )


async def send_whatsapp(
    business_id: str,
    recipient_id: str,
    conversation_id: str,
    message: str,
    branch_id: str = None
):
    payload = {
        "businessId": business_id,
        "conversationId": conversation_id,
        "recipientId": recipient_id,
        "message": message,
    }
    if branch_id:
        payload["branchId"] = branch_id

    await post_with_fallback(
        candidates=_whatsapp_candidates(),
        json=payload,
        headers={"x-api-token": ROBERTO_API_TOKEN},
        log_tag="WHATSAPP",
    )