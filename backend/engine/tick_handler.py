"""
backend/engine/tick_handler.py

Broker-agnostic tick handler that consumes a MarketDataClient instead of
direct ib_insync objects.  Compatible with any provider registered in
backend.engine.market_data.factory.
"""
from __future__ import annotations

import asyncio
import logging
import math
from typing import Dict, Set

from backend.engine.market_data import MarketDataClient
from backend.engine.trade_manager import TradeManager
from backend.engine.indicators import RollingWindow  # keeps existing RW logic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TickHandler:
    """
    Subscribes to real-time ticks for a list of symbols and forwards each tick
    to the TradeManager together with an optional RollingWindow of recent
    prices for indicator-driven stops.
    """

    def __init__(self, md_client: MarketDataClient, trade_manager: TradeManager):
        self.md: MarketDataClient = md_client
        self.trade_manager = trade_manager

        self.subscribed_symbols: Set[str] = set()
        self.tick_queue: asyncio.Queue = asyncio.Queue()

        # per-symbol rolling windows
        self.rolling_windows: Dict[str, RollingWindow] = {}

        # background tasks
        asyncio.create_task(self.process_tick_queue())
        asyncio.create_task(self.validate_subscriptions())

    # --------------------------------------------------------------------- #
    # subscription management
    # --------------------------------------------------------------------- #
    async def subscribe_to_symbols(self, symbols: list[str]) -> None:
        """
        Subscribe to a batch of symbols via the market-data client.
        """
        try:
            for sym in symbols:
                await self.md.subscribe(sym, on_tick=self.on_tick)
            self.subscribed_symbols.update(symbols)
            logger.info(f"Subscribed to ticks for {symbols}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {symbols}: {e}")

    async def validate_subscriptions(self) -> None:
        """
        Heartbeat loop that pings snapshot() once per minute to confirm the
        feed is alive; if snapshot() raises, we resubscribe symbol-by-symbol.
        """
        while True:
            try:
                for symbol in list(self.subscribed_symbols):
                    try:
                        await self.md.snapshot(symbol)  # raises on feed death
                    except Exception:
                        logger.warning(
                            f"Resubscribing to {symbol} after feed drop"
                        )
                        await self.md.subscribe(symbol, on_tick=self.on_tick)
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error validating subscriptions: {e}")
                await asyncio.sleep(10)

    # --------------------------------------------------------------------- #
    # tick ingestion
    # --------------------------------------------------------------------- #
    def on_tick(self, tick: dict) -> None:
        """
        Callback attached to the market-data client.  Non-blocking—just puts
        the tick onto an async queue so heavy processing happens elsewhere.
        """
        asyncio.create_task(self.tick_queue.put(tick))

    async def process_tick_queue(self) -> None:
        """
        Consumes ticks from the queue, updates rolling windows, and calls the
        trade manager’s evaluate logic.
        """
        while True:
            tick = await self.tick_queue.get()
            symbol = tick["symbol"]
            price = tick["price"]

            try:
                if price is None or math.isnan(price):
                    logger.warning(
                        f"Tick received for {symbol}, but price is NaN — skipping"
                    )
                    continue

                # maintain per-symbol rolling window (defaults to 20 if unset)
                rw = self.rolling_windows.setdefault(symbol, RollingWindow(20))
                rw.append(price)

                await self.trade_manager.evaluate_trade_on_tick(
                    symbol, price, rolling_window=rw
                )
            except Exception as e:
                logger.error(f"Error processing tick for {symbol}: {e}")
            finally:
                self.tick_queue.task_done()
