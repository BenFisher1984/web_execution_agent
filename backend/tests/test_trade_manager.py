# backend/tests/test_trade_manager.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
import pytest_asyncio
from backend.engine.trade_manager import TradeManager
from backend.engine.entry_evaluator import EntryEvaluator
from backend.engine.stop_loss_evaluator import StopLossEvaluator
from backend.engine.take_profit_evaluator import TakeProfitEvaluator
from backend.engine.ib_client import IBClient
from backend.config.status_enums import OrderStatus, TradeStatus
from unittest.mock import AsyncMock

@pytest_asyncio.fixture(scope="function")
async def trade_manager(mocker):
    # Mock IBClient to avoid None issues
    ib_client = IBClient()
    mocker.patch.object(ib_client, 'connect', new=AsyncMock(return_value=None))
    mocker.patch.object(ib_client, 'get_last_price', new=AsyncMock(side_effect=lambda symbol: 150.0 if symbol == "AAPL" else None))
    mocker.patch.object(ib_client, 'get_contract_details', new=AsyncMock(return_value=None))

    # Initialize TradeManager with mocked ib_client
    tm = TradeManager(ib_client, config_path="backend/tests/test_trades.json")
    await tm.start()
    
    # Set up evaluators
    tm.entry_evaluator = EntryEvaluator()
    tm.stop_loss_evaluator = StopLossEvaluator()
    tm.take_profit_evaluator = TakeProfitEvaluator()
    
    # Set up test trade data with enum values
    tm.trades = [
        {
            "symbol": "AAPL",
            "direction": "Long",
            "order_status": OrderStatus.ACTIVE.value,
            "trade_status": TradeStatus.PENDING.value,
            "entry_rule": "Custom",
            "entry_rule_price": 150.0,
            "quantity": 100,
            "initial_stop_price": 145.0,
            "take_profit_price": 155.0,
            "take_profit_type": "static",
        }
    ]
    tm.trade_index = {t["symbol"]: t for t in tm.trades}
    
    # Mock file operations and portfolio value
    mocker.patch.object(tm, 'load_portfolio_value', return_value=10000.0)
    mocker.patch.object(tm, 'load_trades', return_value=tm.trades)
    mocker.patch.object(tm, '_save_trades', return_value=None)
    
    yield tm
    
    # Cleanup
    await tm.stop()
    await ib_client.disconnect()

@pytest.mark.asyncio
async def test_entry_trigger(trade_manager):
    # Simulate price hitting entry price
    await trade_manager.evaluate_trade_on_tick("AAPL", 151.0)
    trade = trade_manager.trade_index["AAPL"]
    assert trade["order_status"] == OrderStatus.ENTRY_ORDER_SUBMITTED.value
    assert trade_manager.save_pending is True  # Verify save was triggered

@pytest.mark.asyncio
async def test_entry_no_trigger(trade_manager):
    # Simulate price below entry price
    await trade_manager.evaluate_trade_on_tick("AAPL", 149.0)
    trade = trade_manager.trade_index["AAPL"]
    assert trade["order_status"] == OrderStatus.ACTIVE.value
    assert trade["trade_status"] == TradeStatus.PENDING.value

@pytest.mark.asyncio
async def test_mark_trade_filled_updates(trade_manager):
    # Set trade to submitted state to pass mark_trade_filled check
    trade = trade_manager.trade_index["AAPL"]
    trade["order_status"] = OrderStatus.ENTRY_ORDER_SUBMITTED.value
    
    # Simulate a filled trade
    await trade_manager.mark_trade_filled("AAPL", 151.0, 100)
    trade = trade_manager.trade_index["AAPL"]
    assert trade["trade_status"] == TradeStatus.LIVE.value
    assert trade["order_status"] == OrderStatus.CONTINGENT_ORDER_ACTIVE.value
    assert trade["filled_qty"] == 100
    assert trade["executed_price"] == 151.0
    assert "filled_at" in trade
    assert trade_manager.save_pending is True  # Verify save was triggered