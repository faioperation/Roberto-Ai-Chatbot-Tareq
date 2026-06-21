from core.config import ROBERTO_API_BASE, ROBERTO_API_BASE_PUBLIC, ROBERTO_API_TOKEN
from agent.tools.http_fallback import build_candidates, post_with_fallback


def _facebook_candidates():
    return build_candidates(
        bases=[ROBERTO_API_BASE_PUBLIC, ROBERTO_API_BASE],
        suffixes=[
            "/public/facebook/messages/send",
            "/v1/public/facebook/messages/send",
            "/facebook/messages/send",
        ],
    )


async def send_facebook(
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
        candidates=_facebook_candidates(),
        json=payload,
        headers={"x-api-token": ROBERTO_API_TOKEN},
        log_tag="FACEBOOK",
    )