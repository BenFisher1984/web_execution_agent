import asyncio
from backend.engine.market_data.factory import get_market_data_client

async def main():
    client = get_market_data_client("polygon")
    await client.connect()

    async def print_tick(tick):
        print("Tick received:", tick)

    await client.subscribe_market_data("AAPL", print_tick)

    print("✅ Subscribed to AAPL...streaming live ticks for 30 seconds...")
    await asyncio.sleep(30)
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
