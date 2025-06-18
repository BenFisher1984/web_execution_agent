from engine.ib_client import IBClient
from engine.order_executor import OrderExecutor
from engine.trade_manager import TradeManager

# 🔌 Connect to IB
ib = IBClient()
ib.connect()

# 🧠 Load trades
trade_manager = TradeManager(ib)

# Find a 'triggered' trade
trade = next((t for t in trade_manager.trades if t.get("trade_status") == "triggered"), None)

if not trade:
    print("⚠️ No 'triggered' trade found in saved_trades.json")
    ib.disconnect()
    exit()

symbol = trade["symbol"]
qty = trade.get("quantity", 10)
contract = trade.get("contract")

# ✅ Inject trade manager into executor
executor = OrderExecutor(ib, trade_manager=trade_manager)

# ✅ Submit as real paper trade (not simulated)
order = executor.place_market_order(contract, quantity=qty, trade=trade, what_if=False)

# 🎯 This will call mark_trade_filled() on fill
ib.disconnect()
