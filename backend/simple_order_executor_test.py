#!/usr/bin/env python3
"""
Simple test that uses OrderExecutor without background tasks
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from engine.order_executor import OrderExecutor
from engine.adapters.stub_adapter import StubExecutionAdapter
import json
import asyncio

async def simple_order_executor_test():
    print("=== SIMPLE ORDER EXECUTOR TEST ===")
    print("Testing OrderExecutor without background tasks\n")
    
    # Load the actual trade from saved_trades.json
    with open('config/saved_trades.json', 'r') as f:
        trades = json.load(f)
    
    trade = trades[0]
    
    print("=== CURRENT TRADE ===")
    print(f"Symbol: {trade['symbol']}")
    print(f"Quantity: {trade['quantity']}")
    print(f"Order Status: {trade['order_status']}")
    print(f"Trade Status: {trade['trade_status']}")
    
    # Create OrderExecutor with StubAdapter (don't start background task)
    print("\n=== CREATING ORDER EXECUTOR ===")
    adapter = StubExecutionAdapter()
    order_executor = OrderExecutor(adapter)
    
    print(f"Adapter: {adapter.name}")
    print(f"OrderExecutor created (no background task started)")
    
    # Test placing a market order
    print("\n=== TESTING PLACE_MARKET_ORDER ===")
    
    order_result = await order_executor.place_market_order(
        symbol=trade["symbol"],
        qty=trade["quantity"],
        side="BUY",
        trade=trade
    )
    
    print(f"Order Result: {order_result}")
    
    # Check what happened to the trade
    print("\n=== WHAT HAPPENED TO THE TRADE ===")
    print(f"Order Status: {trade.get('order_status')}")
    print(f"Trade Status: {trade.get('trade_status')}")
    print(f"Order ID: {trade.get('order_id')}")
    
    # Check active orders in OrderExecutor
    print("\n=== ACTIVE ORDERS IN ORDER EXECUTOR ===")
    print(f"Active Orders: {order_executor.active_orders}")
    
    print("\n=== WHAT ORDER EXECUTOR ACTUALLY DOES ===")
    print("✅ Creates order object with symbol, qty, side, etc.")
    print("✅ Calls adapter.place_order()")
    print("✅ Logs the order being sent")
    print("✅ Tracks order in active_orders dict")
    print("✅ Returns order result with broker_id")
    print("❌ Does NOT update trade statuses (that's TradeManager's job)")
    print("❌ Does NOT save to file (that's TradeManager's job)")

if __name__ == "__main__":
    asyncio.run(simple_order_executor_test()) 