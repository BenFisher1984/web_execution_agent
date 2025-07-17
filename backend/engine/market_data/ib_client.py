from __future__ import annotations

import asyncio
import datetime as dt
from collections.abc import AsyncIterator
from typing import Optional

from backend.engine.market_data.base import MarketDataClient, Tick
from backend.engine.adapters.ib_adapter import IBAdapter
import logging

logger = logging.getLogger(__name__)


class IBMarketDataClient(MarketDataClient):
    """
    IB market data client that uses the IB adapter for market data operations.
    Implements the MarketDataClient interface for consistency with other providers.
    """
    name = "ib"

    def __init__(self, ib_adapter=None) -> None:
        # Use shared IB adapter if provided, otherwise create new one
        self._ib_adapter = ib_adapter or IBAdapter(client_id=3)
        self._listeners: dict[str, list] = {}
        self._running = False
        self._tick_queue: asyncio.Queue[Tick] = asyncio.Queue()

    # ---------- lifecycle ----------
    async def connect(self) -> None:
        """Connect to IB Gateway"""
        try:
            # Check if IB adapter is already connected
            if self._ib_adapter.is_connected():
                logger.info("IB adapter already connected, using existing connection")
                self._running = True
                logger.info("IBMarketDataClient connected")
            else:
                # Connect if not already connected
                await self._ib_adapter.connect()
                self._running = True
                logger.info("IBMarketDataClient connected")
        except Exception as e:
            logger.error(f"Failed to connect IBMarketDataClient: {e}")
            # Don't raise - allow the app to continue without IB market data
            self._running = False

    async def disconnect(self) -> None:
        """Disconnect from IB Gateway"""
        try:
            self._running = False
            await self._ib_adapter.disconnect()
            logger.info("IBMarketDataClient disconnected")
        except Exception as e:
            logger.error(f"Failed to disconnect IBMarketDataClient: {e}")

    # ---------- streaming ----------
    async def subscribe(self, symbol: str, *, on_tick: Optional[TickCallback] = None) -> None:
        """Subscribe to real-time market data for a symbol"""
        try:
            # Store callback for this symbol
            if on_tick:
                self._listeners.setdefault(symbol.upper(), []).append(on_tick)
            
            # Subscribe to market data via IB adapter
            await self._ib_adapter.subscribe_market_data(symbol.upper())
            logger.info(f"Subscribed to IB market data for {symbol}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {symbol}: {e}")

    async def unsubscribe(self, symbol: str) -> None:
        """Unsubscribe from market data for a symbol"""
        try:
            self._listeners.pop(symbol.upper(), None)
            await self._ib_adapter.unsubscribe_market_data(symbol.upper())
            logger.info(f"Unsubscribed from IB market data for {symbol}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {symbol}: {e}")

    async def stream_ticks(self) -> AsyncIterator[Tick]:
        """Stream all ticks from IB"""
        while self._running:
            try:
                # This would need to be implemented with IB's real-time data
                # For now, we'll use a polling approach
                await asyncio.sleep(1)
                # Placeholder - would need to implement actual tick streaming
                yield None
            except Exception as e:
                logger.error(f"Error in tick stream: {e}")
                await asyncio.sleep(1)

    # ---------- snapshots ----------
    async def snapshot(self, symbol: str) -> Tick:
        """Get current market snapshot for a symbol"""
        try:
            price = await self._ib_adapter.get_last_price(symbol.upper())
            if price is None:
                raise Exception(f"No price data available for {symbol}")
            
            return {
                "symbol": symbol.upper(),
                "price": price,
                "ts": dt.datetime.utcnow(),
            }
        except Exception as e:
            logger.error(f"Failed to get snapshot for {symbol}: {e}")
            raise

    # ---------- historical data ----------
    async def get_historical_data(self, symbol: str, lookback_days: int):
        """Get historical price data from IB"""
        try:
            bars = await self._ib_adapter.get_historical_data(symbol.upper(), lookback_days)
            if bars is None:
                logger.warning(f"No historical data available for {symbol}")
                return []
            return bars
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return []

    # ---------- contract details ----------
    async def get_contract_details(self, symbol: str):
        """Get contract details from IB"""
        try:
            contract = await self._ib_adapter.get_contract_details(symbol.upper())
            if contract is None:
                logger.warning(f"No contract details available for {symbol}")
                return None
            return contract
        except Exception as e:
            logger.error(f"Failed to get contract details for {symbol}: {e}")
            return None

    # ---------- connection status ----------
    def is_connected(self) -> bool:
        """Check if connected to IB"""
        return self._running and self._ib_adapter.is_connected()

    # ---------- last price ----------
    async def get_last_price(self, symbol: str) -> float:
        """Get latest market price from IB"""
        try:
            if not self.is_connected():
                raise Exception("Not connected to IB")
            price = await self._ib_adapter.get_last_price(symbol.upper())
            if price is None:
                raise Exception(f"No price data available for {symbol}")
            return price
        except Exception as e:
            logger.error(f"Failed to get last price for {symbol}: {e}")
            raise 