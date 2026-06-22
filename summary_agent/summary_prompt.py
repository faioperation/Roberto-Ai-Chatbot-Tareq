def build_summary_prompt(messages: list, subject: str, business_id: str) -> str:
    # Convert messages to readable conversation text
    conversation_text = ""
    for msg in messages:
        role = "Customer" if msg.get("role") == "user" else "Agent"
        content = msg.get("content", "")
        conversation_text += f"{role}: {content}\n"

    subject_label = (subject or "general").strip()

    prompt = f"""
You are a conversation analyst for a multi-tenant business assistant. Analyze the
conversation below and extract structured information.

Business area (subject): {subject_label}
Business ID: {business_id}

Conversation:
{conversation_text}

Extract the following and respond ONLY in valid JSON (no markdown, no backticks,
no extra text). Some fields (pickup_area, destination, weight) only apply to
parcel/cargo shipping — if this conversation is NOT about shipping a parcel, set
them to "Not specified". Do not invent values.

{{
  "items": "what product/service/item the customer wants, or 'Not specified'",
  "pickup_area": "pickup location (parcel/cargo only), or 'Not specified'",
  "destination": "destination (parcel/cargo only), or 'Not specified'",
  "weight": "weight (parcel/cargo only), or 'Not specified'",
  "pickup_date_time": "relevant date/time (pickup, appointment, or delivery) if mentioned, or 'Not specified'",
  "current_status": "one of: Inquiry, Price Quoted, Details Collected, Booking Confirmed, Escalated to Human, Closed",
  "recent_summary": "one sentence summary of the most recent part of the conversation",
  "booking_info": {{
    "booked": true or false,
    "reference": "booking reference if available, else null",
    "price": total price as a number, else null
  }},
  "summary": "2-3 sentence overview of the whole conversation",
  "key_points": ["key point 1", "key point 2", "key point 3"],
  "customer_intent": {{
    "intent": "cold or warm or hot",
    "confidence": "low or medium or high",
    "reason": "one sentence explaining the intent"
  }}
}}

INTENT RULES — read carefully and be conservative. Default to the LOWER intent
when unsure. Most conversations are cold or warm; "hot" must be earned.
- cold: greetings, vague/general questions, just browsing, no specific item or
  details given yet, or only one short message. If in doubt, it is cold.
- warm: customer named a specific product/service AND is actively asking about
  price or details, but has NOT confirmed and has NOT given full contact +
  booking details.
- hot: ONLY if the customer EXPLICITLY confirmed a booking/order/appointment
  ("yes book it", "confirm", "proceed"), OR has provided ALL required details
  AND clearly signalled they want to proceed now. A price quote alone is NOT hot
  — that is warm. Interest alone is NOT hot.

If booking_info.booked is false, the intent is almost never "hot" unless the
customer literally just said to confirm. Match current_status with intent:
"Booking Confirmed" -> hot; "Price Quoted"/"Details Collected" -> usually warm;
"Inquiry" -> usually cold.

Respond with ONLY the JSON object.
"""
    return prompt