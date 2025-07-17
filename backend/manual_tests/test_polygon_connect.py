import asyncio
import websockets
import json
from backend.config.settings import get as settings_get

async def main():
    api_key = settings_get("polygon_api_key", "")
    url = "wss://socket.polygon.io/stocks"

    async with websockets.connect(url) as ws:
        # authenticate
        await ws.send(json.dumps({"action": "auth", "params": api_key}))

        # listen for confirmation
        message = await ws.recv()
        print("✅ Received message:", message)

        data = json.loads(message)
        if isinstance(data, list) and data[0].get("ev") == "status" and data[0].get("status") == "authenticated":
            print("🎉 Polygon WebSocket connection successful and authenticated.")
        else:
            print("⚠️ Polygon authentication failed or returned unexpected status.")

if __name__ == "__main__":
    asyncio.run(main())
