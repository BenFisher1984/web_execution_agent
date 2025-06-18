# tick_handler.py

"""
This module subscribes to real-time market data via IBKR and triggers
trade evaluations on each new tick. It replaces the need for time-based polling.
"""

from ib_insync import Ticker
from backend.engine.ib_client import IBClient
from backend.engine.trade_manager import TradeManager
from backend.engine.order_executor import OrderExecutor
import math  # ✅ For robust NaN checks


class TickHandler:
    def __init__(self, ib_client: IBClient, trade_manager: TradeManager):
        self.ib = ib_client
        self.trade_manager = trade_manager
        self.subscribed_symbols = set()

    def subscribe_to_symbols(self, symbols: list[str]):
        for symbol in symbols:
            if symbol not in self.subscribed_symbols:
                self.ib.subscribe_to_market_data(symbol, self.on_tick)
                self.subscribed_symbols.add(symbol)
                print(f"✅ Subscribed to ticks for {symbol}")

    def on_tick(self, ticker: Ticker):
        symbol = ticker.contract.symbol
        last_price = ticker.last or ticker.close

        # ✅ Defensive check for NaN or missing data
        if last_price is None or math.isnan(last_price):
            print(f"⚠️ Tick received for {symbol}, but price is NaN — skipping")
            return

        print(f"📈 Tick received: {symbol} @ ${last_price:.2f}")
        self.trade_manager.evaluate_trade_on_tick(symbol, last_price)
