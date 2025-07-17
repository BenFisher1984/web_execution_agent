
from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import TypedDict, Literal

from backend.engine.adapters.base import BrokerAdapter, Order, Fill
from backend.config.status_enums import OrderStatus, TradeStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderResult(TypedDict):
    broker_id: str
    local_id: str
    status: str


class OrderExecutor:
    def __init__(self, exec_adapter: BrokerAdapter, trade_manager=None):
        self.adapter: BrokerAdapter = exec_adapter
        self.trade_manager = trade_manager
        self.active_orders: dict[str, dict] = {}  # broker_id → trade data
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if not self._task:
            self._task = asyncio.create_task(self._fill_listener())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    async def place_market_order(
        self,
        symbol: str,
        qty: int,
        side: Literal["BUY", "SELL"] = "BUY",
        tif: Literal["DAY", "GTC"] = "GTC",
        trade: dict | None = None,
    ) -> OrderResult | None:
        order: Order = {
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "order_type": "MARKET",
            "tif": tif,
            "price": None,
        }
        try:
            broker_id = await self.adapter.place_order(order)
            logger.info(f"Market order sent to {self.adapter.name}: {order}")
            if trade:
                self.active_orders[broker_id] = {"trade": trade}
            return {"broker_id": broker_id, "local_id": broker_id, "status": "submitted"}
        except Exception as e:
            logger.error(f"Failed to place market order for {symbol}: {e}")
            return None

    async def submit_exit_order(
        self,
        symbol: str,
        qty: int,
        side: Literal["BUY", "SELL"],
        tif: Literal["DAY", "GTC"] = "GTC",
        trade: dict | None = None,
    ) -> OrderResult | None:
        order: Order = {
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "order_type": "MARKET",
            "tif": tif,
            "price": None,
        }
        try:
            broker_id = await self.adapter.place_order(order)
            logger.info(f"Exit order sent to {self.adapter.name}: {order}")
            if trade:
                self.active_orders[broker_id] = {"trade": trade}
            return {"broker_id": broker_id, "local_id": broker_id, "status": "submitted"}
        except Exception as e:
            logger.error(f"Failed to place exit order for {symbol}: {e}")
            return None

    # ------------------------------------------------------------------ #
    # internal fill pump
    # ------------------------------------------------------------------ #
    async def _fill_listener(self) -> None:
        async for fill in self._stream_fills():
            await self._on_fill(fill)

    async def _stream_fills(self) -> AsyncIterator[Fill]:
        try:
            async for fill in self.adapter.stream_fills():
                if fill is None:
                    logger.debug("Received None fill from adapter")
                    continue
                yield fill
        except asyncio.CancelledError:
            logger.debug("Fill stream cancelled during shutdown")
            raise
        except Exception as e:
            logger.error(f"Fill stream stopped: {e}")

    async def _on_fill(self, fill: Fill) -> None:
        # Handle None fill during shutdown
        if fill is None:
            logger.debug("Received None fill during shutdown")
            return
            
        try:
            broker_id = fill["broker_id"]
            trade_data = self.active_orders.pop(broker_id, None)
            if not trade_data:
                logger.debug(f"Untracked fill {broker_id}")
                return

            trade = trade_data.get("trade")
            symbol = fill["symbol"]

            logger.info(
                f"Fill received for {symbol}: {fill['qty']} @ {fill['price']:.2f}"
            )

            if not trade or not self.trade_manager:
                logger.warning(f"No trade manager to update state for {symbol}")
                return

            if trade.get("order_status") == OrderStatus.CONTINGENT_ORDER_SUBMITTED.value:
                await self.trade_manager.mark_trade_closed(symbol, fill["price"], fill["qty"])
            else:
                await self.trade_manager.mark_trade_filled(symbol, fill["price"], fill["qty"])
        except Exception as e:
            logger.error(f"Error processing fill: {e}")
            return
