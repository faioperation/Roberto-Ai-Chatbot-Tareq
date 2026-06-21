import httpx
from langchain_core.tools import tool
from core.config import ROBERTO_API_BASE, ROBERTO_API_BASE_PUBLIC, ROBERTO_API_TOKEN
from agent.tools.http_fallback import build_candidates, post_with_fallback


# The three booking categories the backend understands.
VALID_CATEGORIES = {"ORDER_BOOKING", "APPOINTMENT_BOOKING", "PARCEL_DELIVERY"}


def _booking_candidates():
    return build_candidates(
        bases=[ROBERTO_API_BASE, ROBERTO_API_BASE_PUBLIC],
        suffixes=[
            "/bookings/create",
            "/public/bookings/create",
            "/v1/public/bookings/create",
        ],
    )


def make_create_booking(branch_id: str = None):

    @tool
    async def create_booking(
        business_id: str,
        category: str,
        customer_name: str,
        customer_number: str,
        price: str,
        email: str = None,
        note: str = None,
        payment_details: dict = None,
        extra_fields: dict = None
    ) -> str:
        """
        IMPORTANT: Call this tool the moment the customer CONFIRMS a booking,
        order, or appointment (e.g. 'confirm', 'book it', 'yes', 'proceed',
        'order it', 'schedule it'). A booking is only created after the customer
        confirms, so by definition the booking is confirmed/booked at this point.

        This single tool creates ALL booking types. YOU must decide which
        category the conversation is, using your own judgement - there is no
        fixed mapping from business type to category. Read the conversation and
        pick the one that fits.

        Parameters:
        - business_id: The business ID from the conversation (required)
        - category: EXACTLY one of these three (required). You decide intelligently:
            * "PARCEL_DELIVERY"     - shipping/sending a physical parcel from a
                                      pickup point to a delivery address.
            * "APPOINTMENT_BOOKING" - booking a meeting / consultation / session
                                      at a date & time, often on a platform
                                      (Zoom, Meet, phone, in-person).
            * "ORDER_BOOKING"       - ordering a product/item to be delivered
                                      (general e-commerce / sales style order).
          If genuinely unsure, prefer the category whose required details the
          customer actually provided.
        - customer_name: Full name of the customer (required)
        - customer_number: Phone number of the customer (required)
        - price: Total price as a string (required; use "0" if genuinely free)
        - email: Customer email (optional)
        - note: Any special instruction or order note (optional)
        - payment_details: Optional dict describing payment. Shape:
            {"paymentMethod": "...", "paymentStatus": "PENDING",
             "transactionId": ""}
          paymentStatus is one of PENDING, COMPLETED, FAILED, REFUNDED.
          If the customer didn't discuss payment, you may omit this or send
          {"paymentStatus": "PENDING"}.
        - extra_fields: A dict holding ALL category-specific details plus any
          other relevant info the customer gave. Use exact camelCase keys.
          The backend saves named standard columns and routes the rest into the
          booking's additional_details automatically. Include only what the
          customer actually provided - never invent values.

          For PARCEL_DELIVERY, relevant keys include:
            pickupAddress, deliveryAddress, deliveryDate, productType,
            productWeight, productHeight, receiverName, receiverPhone,
            insuranceRequired

          For APPOINTMENT_BOOKING, relevant keys include:
            appointmentDate, appointmentTime (ISO 8601 string), platform
            (Zoom/Meet/phone/in-person - ALWAYS ask the customer which platform),
            duration, companyName, industry, timezone, meetingLink

          For ORDER_BOOKING, relevant keys include:
            productType, deliveryDate, deliveryAddress, courierService,
            packageColor, fragile
        """
        # Normalise / validate the category the LLM chose.
        cat = (category or "").strip().upper()
        if cat not in VALID_CATEGORIES:
            print(f"[BOOKING WARN] Unknown category '{category}', "
                  f"defaulting to ORDER_BOOKING")
            cat = "ORDER_BOOKING"

        # --- Required + common fields ---
        payload = {
            "businessId": business_id,
            "category": cat,
            "customerName": customer_name,
            "customerNumber": customer_number,
            "price": str(price),
            # A booking row is created only after the customer confirms,
            # so its status is 'booked'. (Cold/warm/hot intent is a separate
            # concept handled by the summary agent, not here.)
            "orderStatus": "BOOKED",
        }

        if branch_id:
            payload["branchId"] = branch_id
        if email:
            payload["email"] = email
        if note:
            payload["note"] = note

        # --- Payment details (nested object; backend also accepts flat) ---
        if payment_details:
            pd = dict(payment_details)
            pd.setdefault("paymentStatus", "PENDING")
            payload["paymentDetails"] = pd

        # --- Category-specific + dynamic fields (never overwrite common keys) ---
        if extra_fields:
            for k, v in extra_fields.items():
                if k not in payload and v is not None:
                    payload[k] = v

        print(f"[BOOKING] Category: {cat}")
        print(f"[BOOKING] Payload: {payload}")

        try:
            resp = await post_with_fallback(
                candidates=_booking_candidates(),
                json=payload,
                headers={
                    "x-api-token": ROBERTO_API_TOKEN,
                    "Content-Type": "application/json",
                },
                log_tag="BOOKING",
            )

            if resp is not None:
                print(f"[BOOKING] Final status: {resp.status_code}")
                print(f"[BOOKING] Response: {resp.text[:500]}")
                if resp.status_code in (200, 201):
                    return (
                        f"✅ Booking confirmed for {customer_name}!\n"
                        f"💰 Total: {price}\n"
                        f"Our team will contact you at {customer_number} shortly."
                    )

            return (
                f"✅ Booking received!\n"
                f"Our team will contact you at {customer_number} to confirm."
            )

        except Exception as e:
            print(f"[BOOKING ERROR] {e}")
            return (
                f"✅ Booking received!\n"
                f"Our team will contact you at {customer_number} to confirm."
            )

    return create_booking