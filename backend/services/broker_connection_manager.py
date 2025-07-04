import asyncio
import json
from datetime import datetime
import pytz
import logging
from backend.engine.adapters.factory import get_adapter
from backend.config.settings import get as settings_get

logger = logging.getLogger(__name__)

class BrokerConnectionManager:
    def __init__(self, settings_path="backend/config/settings.json"):
        self.adapter = get_adapter(settings_get("execution_adapter"))
        self.settings_path = settings_path
        self.backoff_delay = 1
        self.max_backoff = 60
        self._reconnect_lock = asyncio.Lock()

    def is_connected(self):
        return self.adapter.is_connected()

    async def connect(self):
        try:
            await self.adapter.connect()
            logger.info("✅ Broker connected.")
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")

    async def disconnect(self):
        try:
            await self.adapter.disconnect()
            logger.info("✅ Broker disconnected.")
        except Exception as e:
            logger.error(f"❌ Disconnect failed: {e}")

    async def start_watchdog(self):
        while True:
            if not self.adapter.is_connected():
                if self.in_reset_window():
                    logger.info("⏸ In reset window, skipping reconnect.")
                else:
                    async with self._reconnect_lock:
                        await self.connect()
                    if not self.adapter.is_connected():
                        logger.info(f"🔁 Retrying in {self.backoff_delay} seconds...")
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
            logger.warning(f"⚠️ Failed to check reset window: {e}")
            return False

# Singleton instance
broker_connection_manager = BrokerConnectionManager()
