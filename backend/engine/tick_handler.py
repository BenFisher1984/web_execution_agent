from ib_insync import Ticker
from backend.engine.ib_client import IBClient
from backend.engine.trade_manager import TradeManager
from backend.engine.indicators import RollingWindow  # <-- add this
import math
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TickHandler:
    def __init__(self, ib_client: IBClient, trade_manager: TradeManager):
        self.ib = ib_client
        self.trade_manager = trade_manager
        self.subscribed_symbols = set()
        self.tick_queue = asyncio.Queue()
        asyncio.create_task(self.process_tick_queue())
        asyncio.create_task(self.validate_subscriptions())

        # NEW: store rolling windows per symbol
        self.rolling_windows = {}  # symbol -> RollingWindow

    async def subscribe_to_symbols(self, symbols: list[str]):
        try:
            await self.ib.subscribe_batch_market_data(symbols, self.on_tick)
            self.subscribed_symbols.update(symbols)
            logger.info(f"Subscribed to ticks for {symbols}")
        except Exception as e:
            logger.error(f"Failed to subscribe to symbols {symbols}: {e}")

    async def validate_subscriptions(self):
        while True:
            try:
                for symbol in self.subscribed_symbols:
                    ticker = self.ib.subscribed_contracts.get(symbol)
                    if ticker and not ticker.isActive():
                        logger.warning(f"Resubscribing to {symbol} due to inactive ticker")
                        await self.ib.subscribe_to_market_data(symbol, self.on_tick)
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error validating subscriptions: {e}")
                await asyncio.sleep(10)

    def on_tick(self, ticker: Ticker):
        asyncio.create_task(self.tick_queue.put(ticker))

    async def process_tick_queue(self):
        while True:
            ticker = await self.tick_queue.get()
            try:
                symbol = ticker.contract.symbol
                last_price = ticker.last or ticker.close
                if last_price is None or math.isnan(last_price):
                    logger.warning(f"Tick received for {symbol}, but price is NaN — skipping")
                    continue
                logger.debug(f"Tick received: {symbol} @ ${last_price:.2f}")

                # NEW: rolling window logic
                if symbol in self.rolling_windows:
                    self.rolling_windows[symbol].append(last_price)

                # pass the rolling window to the trade manager
                rolling_window = self.rolling_windows.get(symbol)
                await self.trade_manager.evaluate_trade_on_tick(
                    symbol,
                    last_price,
                    rolling_window=rolling_window  # pass along if available
                )

            except Exception as e:
                logger.error(f"Error processing tick for {symbol}: {e}")
            finally:
                self.tick_queue.task_done()
