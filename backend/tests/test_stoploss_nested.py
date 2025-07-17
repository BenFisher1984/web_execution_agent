import asyncio
from backend.engine.stop_loss_evaluator import StopLossEvaluator
from backend.engine.indicators import RollingWindow

async def test_stop_loss_nested():
    # build a simulated trade exactly like saved_trades.json
    test_trade = {
        "symbol": "AAPL",
        "direction": "Long",
        "initial_stop_price": 180.0,
        "trailing_stop_rules": [{"primary_source": "Price", "condition": "<=", "secondary_source": "EMA 8"}]
    }

    # create a fake rolling window with enough prices
    window = RollingWindow(length=8)
    window.preload([181, 182, 183, 184, 185, 186, 187, 188])  # arbitrary test data

    # instantiate the evaluator
    evaluator = StopLossEvaluator()

    # call it with a fake current price
    result = evaluator.evaluate_stop(test_trade, current_price=185.0, rolling_window=window)

    print("✅ test result:", result)

if __name__ == "__main__":
    asyncio.run(test_stop_loss_nested())
