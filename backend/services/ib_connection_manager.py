import asyncio
import json
from datetime import datetime
import pytz
from backend.engine.ib_client import ib_client

class IBConnectionManager:
    def __init__(self, settings_path="backend/config/settings.json"):
        self.ib = ib_client.ib
        self.settings_path = settings_path
        self.backoff_delay = 1  # Start with 1s
        self.max_backoff = 60   # Cap at 60s
        self.connected = False
        self._reconnect_lock = asyncio.Lock()

    def is_connected(self):
        return self.ib.isConnected()

    async def connect(self):
        try:
            if not self.ib.isConnected():
                print("🔌 Attempting to connect to IB Gateway...")
                await self.ib.connectAsync('127.0.0.1', 7497, clientId=2)
                self.connected = True
                self.backoff_delay = 1
                print("✅ IB Gateway connected.")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False

    async def start_watchdog(self):
        while True:
            if not self.ib.isConnected():
                if self.in_reset_window():
                    print("⏸ IB is in reset window. Suppressing reconnect.")
                else:
                    async with self._reconnect_lock:
                        await self.connect()
                    if not self.ib.isConnected():
                        print(f"🔁 Retrying in {self.backoff_delay} seconds...")
                        await asyncio.sleep(self.backoff_delay)
                        self.backoff_delay = min(self.backoff_delay * 2, self.max_backoff)
                        continue
            await asyncio.sleep(5)

    def in_reset_window(self):
        try:
            with open(self.settings_path) as f:
                config = json.load(f)
            reset_time = config.get("reset_time", "18:00")
            timezone_str = config.get("timezone", "Australia/Sydney")
            tz = pytz.timezone(timezone_str)
            now = datetime.now(tz).strftime("%H:%M")
            return now == reset_time
        except Exception as e:
            print(f"⚠️ Failed to check reset window: {e}")
            return False

# Singleton instance
ib_connection_manager = IBConnectionManager()
