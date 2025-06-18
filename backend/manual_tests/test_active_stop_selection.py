from backend.engine.trade_manager import TradeManager
from ib_insync import Contract
from unittest.mock import MagicMock

def test_active_stop_selection_logic():
    mock_ib = MagicMock()
    trade_manager = TradeManager(mock_ib)

    trade = {
        "symbol": "AAPL",
        "trade_status": "filled",
        "stop_loss": 190.0,
        "trailing_stop": {"price": 210.0},
        "filled_qty": 10,
        "fill_price": 200.0,
        "contract": Contract(symbol="AAPL", secType="STK", exchange="SMART", currency="USD"),
        "volatility": {"adr": 2.0, "atr": 2.1}
    }

    trade_manager.trades = [trade]

    # Simulate tick above trailing stop
    price = 240.0
    trade_manager.evaluate_trade_on_tick("AAPL", price)
    active = trade.get("active_stop")
    assert active is not None, "active_stop should be set"
    assert active["type"] == "trailing_stop", "Expected trailing_stop to be active"

    # Simulate trailing stop falling below stop_loss
    trade["trailing_stop"] = {"price": 180.0}
    price = 200.0
    trade_manager.evaluate_trade_on_tick("AAPL", price)
    active = trade.get("active_stop")
    assert active["type"] == "stop_loss", "Expected stop_loss to be active"

    print("✅ Test passed: active_stop logic responds correctly to tick updates.")

if __name__ == "__main__":
    test_active_stop_selection_logic()
