import asyncio
import traceback
from app.agent import run_round_orchestration_async

async def main():
    print("STARTING")
    try:
        await run_round_orchestration_async(5, "Zlaté jablko sváru", "Kolaps warpového jádra", 1)
    except Exception as e:
        print("CRITICAL ERROR CAUGHT:")
        traceback.print_exc()
    print("FINISHED")

if __name__ == "__main__":
    asyncio.run(main())
