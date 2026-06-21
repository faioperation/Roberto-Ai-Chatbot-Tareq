def build_summary_prompt(messages: list, subject: str, business_id: str) -> str:
    # Convert messages to readable conversation text
    conversation_text = ""
    for msg in messages:
        role = "Customer" if msg.get("role") == "user" else "Agent"
        content = msg.get("content", "")
        conversation_text += f"{role}: {content}\n"

    prompt = f"""
You are a conversation analyst. Analyze the following conversation and extract structured information.

Subject: {subject}
Business ID: {business_id}

Conversation:
{conversation_text}

Extract the following information and respond ONLY in valid JSON format with no extra text:

{{
  "items": "what items/products customer wants to ship or inquire about, or 'Not specified'",
  "pickup_area": "pickup location mentioned by customer, or 'Not specified'",
  "destination": "destination country or city, or 'Not specified'",
  "weight": "weight of items if mentioned, or 'Not specified'",
  "pickup_date_time": "pickup date and time if mentioned, or 'Not specified'",
  "current_status": "one of: Inquiry, Price Quoted, Details Collected, Booking Confirmed, Escalated to Human, Closed",
  "recent_summary": "one sentence summary of the most recent part of conversation",
  "booking_info": {{
    "booked": true or false,
    "reference": "booking reference if available or null",
    "price": total price as number or null
  }},
  "summary": "2-3 sentence overview of the entire conversation",
  "key_points": [
    "key point 1",
    "key point 2",
    "key point 3"
  ],
  "customer_intent": {{
    "intent": "cold or warm or hot",
    "confidence": "low or medium or high",
    "reason": "one sentence explaining why this intent was assigned"
  }}
}}

Intent definitions:
- cold: Customer is just browsing or asking general questions with no commitment
- warm: Customer is interested, asking about pricing or specific details but not confirmed
- hot: Customer confirmed booking or provided all required details ready to book

Respond with ONLY the JSON object. No explanation, no markdown, no backticks.
"""
    return prompt