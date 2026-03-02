import asyncio
from app.agent import run_round_orchestration_async

async def main():
    await run_round_orchestration_async(1, "test fantasy", "test scifi", 2)

if __name__ == "__main__":
    asyncio.run(main())
