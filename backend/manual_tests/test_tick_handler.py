"""
test_tick_handler.py

Full integration test:
- Subscribes to live tick data
- Evaluates trades on tick
- Executes simulated market orders (via order_executor)
"""


from backend.engine.ib_client import IBClient
from backend.engine.trade_manager import TradeManager
from backend.engine.tick_handler import TickHandler
from backend.engine.order_executor import OrderExecutor


def main():
    # 🔌 Connect to IB Gateway
    ib_client = IBClient()
    ib_client.connect()

    # 🧠 Load trades
    trade_manager = TradeManager(ib_client)  # ✅ Construct first

    # 🔁 Create order executor and inject trade manager
    order_executor = OrderExecutor(ib_client, trade_manager=trade_manager)
    trade_manager.order_executor = order_executor  # ✅ Assign back into trade manager

    # ✅ Create tick handler
    tick_handler = TickHandler(ib_client, trade_manager)

    # 📡 Subscribe to tick data for all symbols in trades
    symbols = list({trade.get("symbol") for trade in trade_manager.trades})
    if not symbols:
        print("⚠️ No trades found to subscribe to.")
        return

    tick_handler.subscribe_to_symbols(symbols)

    print("⏳ Running tick handler... (Press Ctrl+C to stop)")
    try:
        ib_client.ib.run()
    except KeyboardInterrupt:
        print("🛑 Interrupted by user.")
    finally:
        ib_client.disconnect()

if __name__ == "__main__":
    main()
