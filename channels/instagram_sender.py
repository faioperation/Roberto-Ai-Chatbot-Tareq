from core.config import ROBERTO_API_BASE, ROBERTO_API_BASE_PUBLIC, ROBERTO_API_TOKEN
from agent.tools.http_fallback import build_candidates, post_with_fallback


def _instagram_candidates():
    return build_candidates(
        bases=[ROBERTO_API_BASE_PUBLIC, ROBERTO_API_BASE],
        suffixes=[
            "/public/instagram/messages/send",
            "/v1/public/instagram/messages/send",
            "/instagram/messages/send",
        ],
    )


async def send_instagram(
    business_id: str,
    recipient_id: str,
    message: str,
    branch_id: str = None
):
    payload = {
        "businessId": business_id,
        "recipientId": recipient_id,
        "message": message,
    }
    if branch_id:
        payload["branchId"] = branch_id

    await post_with_fallback(
        candidates=_instagram_candidates(),
        json=payload,
        headers={"x-api-token": ROBERTO_API_TOKEN},
        log_tag="INSTAGRAM",
    )