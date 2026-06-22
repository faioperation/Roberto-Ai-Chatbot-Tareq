import asyncio
from datetime import datetime
from summary_agent.summary_runner import run_summary_for_all_conversations

# Track if scheduler is running
_scheduler_running = False

# How often the summary job runs (seconds). 1 hour by default.
SUMMARY_INTERVAL_SECONDS = 3600

# Delay before the FIRST run after startup. Short so summaries start flowing
# soon after the server comes up, instead of waiting a full hour.
FIRST_RUN_DELAY_SECONDS = 60


async def start_scheduler():
    global _scheduler_running

    if _scheduler_running:
        print("[SCHEDULER] Already running")
        return

    _scheduler_running = True
    print(f"[SCHEDULER] Started - first run in {FIRST_RUN_DELAY_SECONDS}s, "
          f"then every {SUMMARY_INTERVAL_SECONDS}s")

    # Small initial delay so the app finishes starting and a few messages can
    # land in memory before the first summary pass.
    await asyncio.sleep(FIRST_RUN_DELAY_SECONDS)

    while True:
        try:
            print(f"\n[SCHEDULER] Running summary job at {datetime.now().isoformat()}")
            await run_summary_for_all_conversations()
        except Exception as e:
            print(f"[SCHEDULER ERROR] {e}")

        print(f"[SCHEDULER] Next run in {SUMMARY_INTERVAL_SECONDS}s...")
        await asyncio.sleep(SUMMARY_INTERVAL_SECONDS)