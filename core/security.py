from fastapi import Header, HTTPException
from core.config import AGENT_API_TOKEN

async def verify_token(x_api_token: str = Header(...)):
    # Reject request if token does not match
    if x_api_token != AGENT_API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")