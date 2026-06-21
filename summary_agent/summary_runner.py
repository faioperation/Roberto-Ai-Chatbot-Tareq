import json
import httpx
from datetime import datetime
from openai import OpenAI
from agent.memory import _memory, get_conversation_id
from summary_agent.summary_prompt import build_summary_prompt
from core.config import (
    OPENAI_API_KEY,
    ROBERTO_API_BASE,
    ROBERTO_API_BASE_PUBLIC,
    ROBERTO_API_TOKEN,
)
from agent.tools.http_fallback import build_candidates, post_with_fallback

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def _summary_candidates():
    return build_candidates(
        bases=[ROBERTO_API_BASE_PUBLIC, ROBERTO_API_BASE],
        suffixes=[
            "/public/chat-summaries/upsert",
            "/v1/public/chat-summaries/upsert",
            "/chat-summaries/upsert",
        ],
    )


async def generate_summary(
    conversation_key: str,
    messages: list,
    business_id: str,
    recipient_id: str
) -> dict:
    subject = "cargo"

    prompt = build_summary_prompt(
        messages=messages,
        subject=subject,
        business_id=business_id
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a conversation analyst. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    response_text = response.choices[0].message.content.strip()

    try:
        summary_data = json.loads(response_text)
    except json.JSONDecodeError:
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        summary_data = json.loads(clean_text)

    return summary_data


async def push_summary(
    conversation_id: str,
    business_id: str,
    summary_data: dict
) -> bool:
    try:
        payload = {
            "conversationId": conversation_id,
            "businessId": business_id,
            "items": summary_data.get("items", "Not specified"),
            "pickup_area": summary_data.get("pickup_area", "Not specified"),
            "destination": summary_data.get("destination", "Not specified"),
            "weight": summary_data.get("weight", "Not specified"),
            "pickup_date_time": summary_data.get("pickup_date_time", "Not specified"),
            "current_status": summary_data.get("current_status", "Inquiry"),
            "recent_summary": summary_data.get("recent_summary", ""),
            "booking_info": summary_data.get("booking_info", {
                "booked": False,
                "reference": None,
                "price": None
            }),
            "summary": summary_data.get("summary", ""),
            "key_points": summary_data.get("key_points", []),
            "intent": summary_data.get("customer_intent", {}).get("intent", "cold"),
            "confidence": summary_data.get("customer_intent", {}).get("confidence", "low"),
            "reason": summary_data.get("customer_intent", {}).get("reason", "Not enough information"),
        }

        resp = await post_with_fallback(
            candidates=_summary_candidates(),
            json=payload,
            headers={
                "x-api-token": ROBERTO_API_TOKEN,
                "Content-Type": "application/json",
            },
            log_tag="SUMMARY",
        )

        if resp is not None:
            print(f"[SUMMARY] Push status: {resp.status_code}")
            print(f"[SUMMARY] Response: {resp.text[:200]}")
            return resp.status_code in (200, 201)
        return False

    except Exception as e:
        print(f"[SUMMARY ERROR] {e}")
        return False


async def run_summary_for_all_conversations():
    print(f"\n[SUMMARY JOB] Starting at {datetime.now().isoformat()}")
    print(f"[SUMMARY JOB] Total conversations in memory: {len(_memory)}")

    if not _memory:
        print("[SUMMARY JOB] No conversations found in memory")
        return

    success_count = 0
    fail_count = 0

    for conversation_key, messages in _memory.items():
        if not messages:
            continue

        parts = conversation_key.split("_")
        if len(parts) != 2:
            continue

        business_id = parts[0]
        recipient_id = parts[1]

        conversation_id = get_conversation_id(business_id, recipient_id)

        print(f"\n[SUMMARY JOB] Processing: {conversation_key}")
        print(f"[SUMMARY JOB] Conversation ID: {conversation_id}")
        print(f"[SUMMARY JOB] Messages count: {len(messages)}")

        try:
            summary_data = await generate_summary(
                conversation_key=conversation_key,
                messages=messages,
                business_id=business_id,
                recipient_id=recipient_id
            )

            print(f"[SUMMARY JOB] Intent: {summary_data.get('customer_intent', {}).get('intent')}")
            print(f"[SUMMARY JOB] Status: {summary_data.get('current_status')}")

            success = await push_summary(
                conversation_id=conversation_id,
                business_id=business_id,
                summary_data=summary_data
            )

            if success:
                success_count += 1
                print(f"[SUMMARY JOB] OK Summary pushed for {conversation_key}")
            else:
                fail_count += 1
                print(f"[SUMMARY JOB] FAIL push for {conversation_key}")

        except Exception as e:
            fail_count += 1
            print(f"[SUMMARY JOB] ERROR for {conversation_key}: {e}")

    print(f"\n[SUMMARY JOB] Completed - Success: {success_count} | Failed: {fail_count}")