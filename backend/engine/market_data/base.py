"""
Neutral market-data interface.

All strategy/engine code must depend on **MarketDataClient**, never on a
concrete SDK.  Each real provider (IB, Polygon, dxFeed …) subclasses this.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Protocol, TypedDict


class Tick(TypedDict):
    """Minimal shape we guarantee to strategies."""
    symbol: str
    price: float
    ts: datetime


class MarketDataClient(ABC):
    """Abstract base for every real-time data feed."""

    name: str  # short slug, e.g. "ib", "polygon"

    # ---------- lifecycle ----------
    @abstractmethod
    async def connect(self) -> None: ...
    @abstractmethod
    async def disconnect(self) -> None: ...

    # ---------- streaming ----------
    @abstractmethod
    async def subscribe(
        self,
        symbol: str,
        *,
        on_tick: "TickCallback | None" = None,
    ) -> None: ...
    @abstractmethod
    async def unsubscribe(self, symbol: str) -> None: ...
    
    @abstractmethod
    async def stream_ticks(self) -> AsyncIterator[Tick]:
        """
        Optional pull-style interface: async iterate over all ticks the client
        receives, regardless of subscription method.
        """
        ...

    # ---------- snapshots ----------
    @abstractmethod
    async def snapshot(self, symbol: str) -> Tick: ...


class TickCallback(Protocol):
    def __call__(self, tick: Tick) -> None: ...
