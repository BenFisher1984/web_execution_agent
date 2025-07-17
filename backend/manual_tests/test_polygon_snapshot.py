import asyncio
import aiohttp
from backend.config.settings import get as settings_get

async def main():
    api_key = settings_get("polygon_api_key", "")
    url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/AAPL?apiKey={api_key}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            print("✅ Snapshot received:")
            print(data)

if __name__ == "__main__":
    asyncio.run(main())
