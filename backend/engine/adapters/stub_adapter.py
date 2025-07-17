from __future__ import annotations
import asyncio, datetime as dt, itertools, random
from collections.abc import AsyncIterator

from backend.engine.adapters.base import BrokerAdapter, Order, Fill, Position


class StubExecutionAdapter(BrokerAdapter):
    """
    No-op adapter that pretends to route orders and immediately fills them
    at a random price. Handy for local dev when no broker is live.
    """

    name = "stub"

    def __init__(self) -> None:
        self._next_id = itertools.count(1)
        self._fill_queue: asyncio.Queue[Fill] = asyncio.Queue()
        self._positions: dict[str, Position] = {}
        super().__init__(name="stub")


    # ---------- lifecycle ----------
    async def connect(self) -> None:
        # nothing to do
        ...

    async def disconnect(self) -> None:
        # nothing to do
        ...

    def is_connected(self) -> bool:
        # always "connected" for the stub
        return True

    # ---------- order routing ----------
    async def place_order(self, order: Order) -> str:
        broker_id = f"STUB-{next(self._next_id)}"

        # Immediately create a fill
        price = order["price"] or random.uniform(90, 110)
        fill: Fill = {
            "symbol": order["symbol"],
            "qty": order["qty"],
            "price": price,
            "ts": dt.datetime.utcnow(),
            "broker_id": broker_id,
            "local_id": broker_id,
        }
        await self._fill_queue.put(fill)

        # maintain naive position
        pos = self._positions.setdefault(
            order["symbol"],
            {"symbol": order["symbol"], "qty": 0, "avg_price": price},
        )
        pos["qty"] += order["qty"]
        pos["avg_price"] = price

        return broker_id

    async def execute_order(self, order_details):
        # identical to place_order for stub
        return await self.place_order(order_details)

    async def get_order_status(self, order_id):
        # pretend all orders fill instantly
        return {"order_id": order_id, "status": "filled"}

    async def cancel_order(self, broker_id: str) -> None:
        # No-op: orders are immediately filled
        ...

    async def stream_fills(self) -> AsyncIterator[Fill]:
        while True:
            yield await self._fill_queue.get()

    # ---------- account ----------
    async def get_positions(self) -> list[Position]:
        return list(self._positions.values())

    # ---------- market helpers ----------
    async def get_market_price(self, symbol: str) -> float:
        return random.uniform(90, 110)

    async def get_history(self, symbol: str, days: int) -> list[float]:
        return [random.uniform(90, 110) for _ in range(days)]

    async def get_contract_details(self, symbol: str):
        # dummy contract details
        return {"symbol": symbol}

    async def get_last_price(self, symbol: str):
        return random.uniform(90, 110)

    async def get_historical_data(self, symbol: str, lookback_days: int):
        return [
            {"symbol": symbol, "price": random.uniform(90, 110)}
            for _ in range(lookback_days)
        ]

    async def get_contract_details_batch(self, symbols: list[str]):
        return {symbol: {"symbol": symbol} for symbol in symbols}

    async def subscribe_market_data(self, symbol):
        # nothing to do
        ...

    async def unsubscribe_market_data(self, symbol):
        # nothing to do
        ...
