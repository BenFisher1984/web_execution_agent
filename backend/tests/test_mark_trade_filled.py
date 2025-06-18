# test_mark_trade_filled.py

from backend.engine.ib_client import IBClient
from backend.engine.trade_manager import TradeManager
import json

CONFIG_PATH = "backend/config/saved_trades.json"

ib = IBClient()
ib.connect()

trade_manager = TradeManager(ib)

# Find a triggered trade
trade = next((t for t in trade_manager.trades if t.get("trade_status") == "triggered"), None)

if not trade:
    print("⚠️ No 'triggered' trade found to simulate fill.")
    ib.disconnect()
    exit()

symbol = trade["symbol"]
qty = trade.get("quantity", 10)
simulated_price = 197.17

print(f"🔧 Simulating post-fill for {symbol} at ${simulated_price} x {qty}")
trade_manager.mark_trade_filled(symbol=symbol, fill_price=simulated_price, filled_qty=qty)

# 🔍 Reload and assert changes
with open(CONFIG_PATH, "r") as f:
    updated_trades = json.load(f)

updated = next((t for t in updated_trades if t.get("symbol") == symbol), None)

assert updated, "❌ Trade not found after update"
assert updated.get("trade_status") == "filled", "❌ Status not updated to 'filled'"
assert updated.get("fill_price") == simulated_price, "❌ Fill price not recorded"
assert updated.get("filled_qty") == qty, "❌ Filled quantity not recorded"
assert "stop_loss" in updated, "❌ Stop loss not set"
assert "trailing_stop" in updated, "❌ Trailing stop not set"

print("✅ Trade update validated successfully.")

ib.disconnect()
