from collections import defaultdict

_memory = defaultdict(list)
_conversation_ids = {}

# Stores the real subject per conversation so the summary job can analyse each
# conversation with the correct business context (instead of hardcoded "cargo").
_subjects = {}


def get_history(business_id: str, recipient_id: str) -> list:
    key = f"{business_id}_{recipient_id}"
    return _memory[key]


def save_message(business_id: str, recipient_id: str, role: str, content: str):
    key = f"{business_id}_{recipient_id}"
    _memory[key].append({"role": role, "content": content})


def save_conversation_id(business_id: str, recipient_id: str, conversation_id: str):
    key = f"{business_id}_{recipient_id}"
    _conversation_ids[key] = conversation_id


def get_conversation_id(business_id: str, recipient_id: str):
    """
    Returns the real backend conversation UUID if we have one, otherwise None.

    IMPORTANT: we deliberately return None (not recipient_id) when unknown.
    The recipient_id is a phone/channel id, NOT a conversation UUID, so using it
    as conversationId made summary upserts target a non-existent conversation and
    silently fail. Callers must handle None (skip push / log) instead.
    """
    key = f"{business_id}_{recipient_id}"
    return _conversation_ids.get(key)


def save_subject(business_id: str, recipient_id: str, subject: str):
    key = f"{business_id}_{recipient_id}"
    if subject:
        _subjects[key] = subject


def get_subject(business_id: str, recipient_id: str) -> str:
    key = f"{business_id}_{recipient_id}"
    return _subjects.get(key, "")


def clear_history(business_id: str, recipient_id: str):
    key = f"{business_id}_{recipient_id}"
    _memory[key] = []