from collections import defaultdict

_memory = defaultdict(list)
_conversation_ids = {}

def get_history(business_id: str, recipient_id: str) -> list:
    key = f"{business_id}_{recipient_id}"
    return _memory[key]

def save_message(business_id: str, recipient_id: str, role: str, content: str):
    key = f"{business_id}_{recipient_id}"
    _memory[key].append({"role": role, "content": content})

def save_conversation_id(business_id: str, recipient_id: str, conversation_id: str):
    key = f"{business_id}_{recipient_id}"
    _conversation_ids[key] = conversation_id

def get_conversation_id(business_id: str, recipient_id: str) -> str:
    key = f"{business_id}_{recipient_id}"
    return _conversation_ids.get(key, recipient_id)

def clear_history(business_id: str, recipient_id: str):
    key = f"{business_id}_{recipient_id}"
    _memory[key] = []