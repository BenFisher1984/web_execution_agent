#!/usr/bin/env python3
"""
Test showing how OrderExecutor passes fill information back to TradeManager
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from engine.order_executor import OrderExecutor
from engine.trade_manager import TradeManager
from engine.adapters.stub_adapter import StubExecutionAdapter
import json
import asyncio

async def test_fill_flow():
    print("=== TESTING FILL FLOW ===")
    print("OrderExecutor → TradeManager fill communication\n")
    
    # Load the actual trade from saved_trades.json
    with open('config/saved_trades.json', 'r') as f:
        trades = json.load(f)
    
    trade = trades[0]
    
    print("=== CURRENT TRADE ===")
    print(f"Symbol: {trade['symbol']}")
    print(f"Quantity: {trade['quantity']}")
    print(f"Order Status: {trade['order_status']}")
    print(f"Trade Status: {trade['trade_status']}")
    
    # Create components
    print("\n=== CREATING COMPONENTS ===")
    adapter = StubExecutionAdapter()
    trade_manager = TradeManager(adapter, config_path="config/saved_trades.json")
    order_executor = OrderExecutor(adapter, trade_manager)
    
    print(f"Adapter: {adapter.name}")
    print(f"TradeManager created")
    print(f"OrderExecutor created with TradeManager reference")
    
    # Place order
    print("\n=== PLACING ORDER ===")
    order_result = await order_executor.place_market_order(
        symbol=trade["symbol"],
        qty=trade["quantity"],
        side="BUY",
        trade=trade
    )
    
    print(f"Order Result: {order_result}")
    print(f"Active Orders: {order_executor.active_orders}")
    
    # Simulate fill (in real system, this comes from broker)
    print("\n=== SIMULATING FILL ===")
    print("In real system, broker sends fill to adapter")
    print("Adapter streams fill to OrderExecutor")
    print("OrderExecutor calls TradeManager.mark_trade_filled()")
    
    # Check what TradeManager.mark_trade_filled() would do
    print("\n=== WHAT TRADE MANAGER WOULD DO ===")
    print("TradeManager.mark_trade_filled() would:")
    print("1. Update trade status to 'Filled'")
    print("2. Update trade status to 'Live'")
    print("3. Set filled_qty and executed_price")
    print("4. Save updated trade to saved_trades.json")
    
    print("\n=== FILL FLOW SUMMARY ===")
    print("1. OrderExecutor places order → tracks in active_orders")
    print("2. Broker sends fill → adapter.stream_fills()")
    print("3. OrderExecutor._on_fill() receives fill")
    print("4. OrderExecutor calls TradeManager.mark_trade_filled()")
    print("5. TradeManager updates trade status and saves to file")

if __name__ == "__main__":
    asyncio.run(test_fill_flow()) 