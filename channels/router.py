from channels.whatsapp_sender import send_whatsapp
from channels.facebook_sender import send_facebook
from channels.instagram_sender import send_instagram

async def send_response(
    channel: str,
    business_id: str,
    recipient_id: str,
    conversation_id: str,
    message: str,
    branch_id: str = None
):

    if channel == "whatsapp":
        await send_whatsapp(business_id, recipient_id, conversation_id, message, branch_id)
    
    elif channel == "facebook":
        await send_facebook(business_id, recipient_id, message, branch_id)
    
    elif channel == "instagram":
        await send_instagram(business_id, recipient_id, message, branch_id)
    
    else:
        print(f"Unknown channel received: {channel}")