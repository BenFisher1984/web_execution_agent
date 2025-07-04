from __future__ import annotations

import asyncio
import datetime as dt
import random
from collections.abc import AsyncIterator

from backend.engine.market_data.base import MarketDataClient, Tick

_PING_INTERVAL = 0.5  # seconds


class StubMarketDataClient(MarketDataClient):
    """
    Dummy market-data provider that emits a random price every 500 ms.
    Drives the new TickHandler without any external API keys.
    """
    name = "stub"

    def __init__(self) -> None:
        self._listeners: dict[str, list] = {}
        self._running = False

    # ---------- lifecycle ----------
    async def connect(self) -> None:
        self._running = True
        asyncio.create_task(self._tick_pump())

    async def disconnect(self) -> None:
        self._running = False

    # ---------- streaming ----------
    async def subscribe(self, symbol: str, *, on_tick=None) -> None:
        self._listeners.setdefault(symbol.upper(), []).append(on_tick)

    async def unsubscribe(self, symbol: str) -> None:
        self._listeners.pop(symbol.upper(), None)

    async def stream_ticks(self) -> AsyncIterator[Tick]:
        """
        Optional pull-style iterator (not required by TickHandler).
        Mirrors every tick injected into callbacks so tests can consume a stream.
        """
        queue: asyncio.Queue[Tick] = asyncio.Queue()

        async def enqueue(tick: Tick):
            await queue.put(tick)

        # subscribe all current symbols so we mirror their ticks
        for sym in self._listeners.keys():
            await self.subscribe(sym, on_tick=enqueue)

        while True:
            yield await queue.get()

    # ---------- snapshots ----------
    async def snapshot(self, symbol: str) -> Tick:
        return _make_tick(symbol)

    # ---------- internals ----------
    async def _tick_pump(self) -> None:
        while self._running:
            await asyncio.sleep(_PING_INTERVAL)
            for sym, callbacks in list(self._listeners.items()):
                tick = _make_tick(sym)
                for cb in callbacks:
                    if cb:
                        cb(tick)


def _make_tick(symbol: str) -> Tick:
    return {
        "symbol": symbol.upper(),
        "price": random.uniform(90, 110),
        "ts": dt.datetime.utcnow(),
    }
