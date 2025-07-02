import asyncio
from backend.engine.ib_client import ib_client
from backend.engine.order_executor import OrderExecutor
from backend.engine.trade_manager import TradeManager
from backend.engine.tick_handler import TickHandler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_test():
    try:
        # 1️⃣ Connect
        await ib_client.connect()
        logger.info("Connected to IB Gateway")

        # 2️⃣ Create managers
        trade_manager = TradeManager(ib_client)
        order_executor = OrderExecutor(ib_client, trade_manager)
        tick_handler = TickHandler(ib_client, trade_manager)

        # 3️⃣ Subscribe to a batch of tickers
        symbols = ["AAPL", "MSFT", "GOOG"]
        await tick_handler.subscribe_to_symbols(symbols)

        # 4️⃣ Preload volatility (will cache)
        await trade_manager.preload_volatility()

        # 5️⃣ Test market order with whatIf
        result = await order_executor.place_market_order("AAPL", 1, trade={"symbol": "AAPL"}, what_if=True)
        if result:
            logger.info("Test market order submitted in whatIf mode")
        else:
            logger.error("Test order failed")

        # 6️⃣ Test contract cache
        cached_contract = await ib_client.get_contract_details("AAPL")
        logger.info(f"Confirmed contract cache for AAPL: {cached_contract}")

        # 7️⃣ Test volatility cache
        cached_vol = ib_client.volatility_cache.get("AAPL")
        if cached_vol:
            logger.info(f"Confirmed volatility cache for AAPL: {cached_vol}")
        else:
            logger.warning("Volatility cache missing for AAPL")

        # 8️⃣ Give it a few seconds to print any tick events
        await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        # Ensure disconnection
        await ib_client.disconnect()
        logger.info("Test complete")

if __name__ == "__main__":
    asyncio.run(run_test())