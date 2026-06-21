import asyncio
import uvicorn
from fastapi import FastAPI
from routes.agent_routes import router as agent_router
from routes.summary_routes import router as summary_router
from summary_agent.scheduler import start_scheduler

app = FastAPI(title="AI Agent")

# Register routes
app.include_router(agent_router, prefix="/api")
app.include_router(summary_router, prefix="/api")


# Start scheduler when app starts
@app.on_event("startup")
async def startup_event():
    # Start background scheduler for summary job
    asyncio.create_task(start_scheduler())
    print("[STARTUP] Summary scheduler started")

@app.get("/")
async def root():
    return {"message": "AI Agent is running!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=False)
