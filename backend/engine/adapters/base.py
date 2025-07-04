# backend/engine/adapters/base.py

from abc import ABC, abstractmethod
from typing import TypedDict

class Order(TypedDict):
    symbol: str
    side: str
    qty: int
    order_type: str
    tif: str
    price: float | None

class Fill(TypedDict):
    broker_id: str
    symbol: str
    qty: int
    price: float
    ts: object  # datetime or similar
    local_id: str

class Position(TypedDict):
    symbol: str
    qty: int
    avg_price: float

class BrokerAdapter(ABC):

    @abstractmethod
    async def connect(self):
        """
        Connect to broker platform.
        """
        pass

    @abstractmethod
    async def disconnect(self):
        """
        Disconnect from broker platform.
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if currently connected to broker.
        Returns True if connected, False otherwise.
        """
        pass

    @abstractmethod
    async def get_contract_details(self, symbol: str):
        """
        Retrieve detailed information about a specific ticker symbol.
        Returns details needed for placing an order.
        """
        pass

    @abstractmethod
    async def execute_order(self, order_details):
        """
        Submit an order (buy/sell).
        """
        pass

    @abstractmethod
    async def get_order_status(self, order_id):
        """
        Check status of an existing order.
        """
        pass

    @abstractmethod
    async def subscribe_market_data(self, symbol):
        """
        Subscribe to live price updates for a symbol.
        """
        pass

    @abstractmethod
    async def unsubscribe_market_data(self, symbol):
        """
        Unsubscribe from live price updates for a symbol.
        """
        pass

    @abstractmethod
    async def get_last_price(self, symbol: str):
        """
        Get latest market price for a symbol.
        """
        pass

    @abstractmethod
    async def get_historical_data(self, symbol: str, lookback_days: int):
        """
        Fetch historical price data for a symbol.
        """
        pass
