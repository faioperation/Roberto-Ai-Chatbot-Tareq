import asyncio
from datetime import datetime
from summary_agent.summary_runner import run_summary_for_all_conversations

# Track if scheduler is running
_scheduler_running = False

async def start_scheduler():
    global _scheduler_running

    if _scheduler_running:
        print("[SCHEDULER] Already running")
        return

    _scheduler_running = True
    print("[SCHEDULER] Started — will run every 1 hour")

    while True:
        try:
            print(f"\n[SCHEDULER] Running summary job at {datetime.now().isoformat()}")
            await run_summary_for_all_conversations()
        except Exception as e:
            print(f"[SCHEDULER ERROR] {e}")

        # Wait 1 hour before next run
        print("[SCHEDULER] Next run in 1 hour...")
        await asyncio.sleep(3600)  # 3600 seconds = 1 hour