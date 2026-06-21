import time
import httpx
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from agent.memory import get_history, save_message, save_conversation_id
from agent.prompt_builder import build_prompt
from agent.tools import get_all_tools
from agent.tools.http_fallback import build_candidates, get_with_fallback
from rag.retriever import retrieve
from channels.router import send_response
from core.config import (
    OPENAI_API_KEY,
    ROBERTO_API_BASE,
    ROBERTO_API_BASE_PUBLIC,
    ROBERTO_API_TOKEN,
)

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o",
    api_key=OPENAI_API_KEY,
    temperature=0.7
)

# Caches with TTL. Because business training / pricing data is dynamic and can
# be updated by the admin at any time, we expire cached entries after TTL so the
# agent picks up changes without needing a restart.
CACHE_TTL_SECONDS = 300  # 5 minutes

_business_cache = {}   # business_id -> (timestamp, data)
_training_cache = {}   # business_id -> (timestamp, data)


def _cache_get(cache: dict, key: str):
    entry = cache.get(key)
    if not entry:
        return None
    ts, value = entry
    if (time.time() - ts) > CACHE_TTL_SECONDS:
        cache.pop(key, None)
        return None
    return value


def _cache_set(cache: dict, key: str, value):
    cache[key] = (time.time(), value)


def _business_candidates(business_id: str):
    return build_candidates(
        bases=[ROBERTO_API_BASE, ROBERTO_API_BASE_PUBLIC],
        suffixes=[
            f"/business/{business_id}",
            f"/public/business/{business_id}",
            f"/v1/public/business/{business_id}",
        ],
    )


def _training_candidates(business_id: str):
    # Documented: {base_with_v1}/public/agent-training/{business_id}
    return build_candidates(
        bases=[ROBERTO_API_BASE_PUBLIC, ROBERTO_API_BASE],
        suffixes=[
            f"/public/agent-training/{business_id}",
            f"/v1/public/agent-training/{business_id}",
            f"/agent-training/{business_id}",
        ],
    )


async def fetch_business(business_id: str) -> dict:
    cached = _cache_get(_business_cache, business_id)
    if cached is not None:
        return cached

    try:
        resp = await get_with_fallback(
            candidates=_business_candidates(business_id),
            headers={"x-api-token": ROBERTO_API_TOKEN},
            log_tag="FETCH BUSINESS",
        )
        if resp is not None and resp.status_code == 200:
            data = resp.json()
            _cache_set(_business_cache, business_id, data)
            return data
    except Exception as e:
        print(f"[FETCH BUSINESS ERROR] {e}")

    return {}


async def fetch_training_data(business_id: str) -> dict:
    cached = _cache_get(_training_cache, business_id)
    if cached is not None:
        return cached

    try:
        resp = await get_with_fallback(
            candidates=_training_candidates(business_id),
            headers={
                "x-api-token": ROBERTO_API_TOKEN,
                "Content-Type": "application/json",
            },
            log_tag="FETCH TRAINING",
        )

        if resp is not None and resp.status_code == 200:
            payload = resp.json()
            data = payload.get("data", {})

            training_config = {
                "systemPrompt": data.get("systemPrompt", ""),
                "businessInformation": data.get("businessInformation", ""),
                "rowText": data.get("rowText", ""),
                "productInformation": " ".join([
                    item.get("rowText", "")
                    for item in data.get("productInformation", [])
                    if item.get("rowText")
                ]),
                "policiesGuidelines": " ".join([
                    item.get("rowText", "")
                    for item in data.get("policiesGuidelines", [])
                    if item.get("rowText")
                ]),
                "faq": " ".join([
                    item.get("rowText", "")
                    for item in data.get("faq", [])
                    if item.get("rowText")
                ]),
            }

            print(f"[FETCH TRAINING] systemPrompt: {training_config['systemPrompt'][:50]}")
            print(f"[FETCH TRAINING] rowText length: {len(training_config['rowText'])}")

            _cache_set(_training_cache, business_id, training_config)
            return training_config

    except Exception as e:
        print(f"[FETCH TRAINING ERROR] {e}")

    return {}


async def run_agent(
    business_id: str,
    training_data_id: str,
    subject: str,
    recipient_id: str,
    conversation_id: str,
    channel: str,
    message: str,
    branch_id: str = None
):
    # ── Step 1: Fetch business profile ──────────────────────────────
    business_data = await fetch_business(business_id)
    business_profile = business_data.get("profile", None)

    # ── Step 2: Fetch training config using business_id ──────────────
    training_config = await fetch_training_data(business_id)

    # ── Step 3: Decide knowledge source ──────────────────────────────
    context = None
    if training_config:
        print(f"[KNOWLEDGE SOURCE] Using business training config")
    else:
        context = await retrieve(message, subject)
        print(f"[KNOWLEDGE SOURCE] Using Pinecone base-{subject}")

    # ── Step 4: Build system prompt ───────────────────────────────────
    system_prompt = build_prompt(
        subject=subject,
        business_profile=business_profile,
        training_config=training_config if training_config else None,
        context=context
    )

    # Always inject actual business_id so agent never guesses it
    # This prevents agent from making up wrong business IDs
    system_prompt += f"\n\nCRITICAL: The business_id for this conversation is: {business_id}"
    system_prompt += f"\nAlways use this exact business_id when calling collect_lead or create_booking tools."
    system_prompt += f"\nNever use any other business_id or make one up."

    # Inject branch_id if available — prevents agent from guessing or skipping it
    if branch_id:
        system_prompt += f"\n\nCRITICAL: The branch_id for this conversation is: {branch_id}"
        system_prompt += f"\nAlways pass this exact branch_id when calling collect_lead or create_booking tools."
    else:
        system_prompt += f"\n\nNote: No branch_id is available for this conversation. Do not pass a branch_id to collect_lead or create_booking tools."

    # ── Step 5: Load conversation history ────────────────────────────
    history = get_history(business_id, recipient_id)

    # ── Step 6: Build messages with history ──────────────────────────
    all_messages = []
    for h in history:
        all_messages.append(h)
    all_messages.append({"role": "user", "content": message})

    # ── Step 7: Run LangGraph ReAct agent ────────────────────────────
    # branch_id is bound directly into the tools at creation time —
    # the LLM never has to pass it itself, so it can never be dropped
    tools = get_all_tools(business_id=business_id, branch_id=branch_id)

    agent = create_react_agent(
        llm,
        tools,
        prompt=system_prompt
    )
    result = await agent.ainvoke({"messages": all_messages})

    # ── Step 8: Extract final response ───────────────────────────────
    ai_response = result["messages"][-1].content

    # ── Step 9: Log for testing ───────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"Business ID  : {business_id}")
    print(f"Branch ID    : {branch_id}")
    print(f"Subject      : {subject}")
    print(f"Channel      : {channel}")
    print(f"Recipient    : {recipient_id}")
    print(f"Customer Msg : {message}")
    print(f"AI Response  : {ai_response}")
    print(f"{'='*50}\n")

    # ── Step 10: Save to memory ───────────────────────────────────────
    save_message(business_id, recipient_id, "user", message)
    save_message(business_id, recipient_id, "assistant", ai_response)

    # ── Step 11: Save conversation_id ────────────────────────────────
    if conversation_id:
        save_conversation_id(business_id, recipient_id, conversation_id)

    # ── Step 12: Send response to correct channel ─────────────────────
    # Re-check pause state — it may have changed while the agent was
    # processing (e.g. a human agent took over mid-conversation).
    # Import here to avoid circular imports at module level.
    from webhooks.incoming import paused_conversations as _paused
    _pause_key = f"{business_id}:{recipient_id}"
    if _pause_key in _paused:
        print(f"[HANDOFF] AI paused mid-processing for {_pause_key} — response suppressed, not sent to channel")
        # Still return the response so the API caller gets it,
        # but we do NOT send it to the customer's channel.
        return ai_response

    await send_response(
        channel=channel,
        business_id=business_id,
        recipient_id=recipient_id,
        conversation_id=conversation_id,
        message=ai_response,
        branch_id=branch_id
    )

    # ── Step 13: Return response ──────────────────────────────────────
    return ai_response