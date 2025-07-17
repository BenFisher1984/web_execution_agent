#!/usr/bin/env python3
"""
Corrected trade demo using proper architecture: OrderExecutor → StubAdapter
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from engine.entry_evaluator import EntryEvaluator
from engine.order_executor import OrderExecutor
from engine.adapters.stub_adapter import StubExecutionAdapter
import json
import asyncio

async def corrected_trade_demo():
    print("=== CORRECTED TRADE DEMO ===")
    print("Proper Architecture: OrderExecutor → StubAdapter\n")
    
    # 1. Create a simple trade
    trade = {
        "symbol": "AAPL",
        "quantity": 100,
        "direction": "Long",
        "order_status": "Working",
        "trade_status": "Pending",
        "entry_rules": [{"type": "PRICE_ABOVE", "price": 150.00}],
        "initial_stop_rules": [{"type": "PRICE_BELOW", "price": 140.00}],
        "trailing_stop_rules": [{"type": "PRICE_ABOVE", "price": 160.00}],
        "take_profit_rules": [{"type": "PRICE_BELOW", "price": 170.00}]
    }
    
    print("1. INITIAL TRADE:")
    print(f"   Symbol: {trade['symbol']}")
    print(f"   Quantity: {trade['quantity']}")
    print(f"   Order Status: {trade['order_status']}")
    print(f"   Trade Status: {trade['trade_status']}")
    print(f"   Entry Rule: {trade.get('entry_rules', [{}])[0]}")
    print(f"   Initial Stop Rule: {trade.get('initial_stop_rules', [{}])[0]}")
    print(f"   Trailing Stop Rule: {trade.get('trailing_stop_rules', [{}])[0]}")
    print(f"   Take Profit Rule: {trade.get('take_profit_rules', [{}])[0]}")
    
    # 2. Evaluate entry condition
    print("\n2. EVALUATING ENTRY CONDITION:")
    entry_eval = EntryEvaluator()
    current_price = 155.00  # Above entry price
    
    print(f"   Current Price: ${current_price}")
    entry_triggered = entry_eval.should_trigger_entry(trade, current_price)
    print(f"   Entry Triggered: {entry_triggered}")
    
    if entry_triggered:
        # 3. Execute order using OrderExecutor
        print("\n3. EXECUTING ORDER (via OrderExecutor):")
        
        # Create adapter and order executor
        adapter = StubExecutionAdapter()
        order_executor = OrderExecutor(adapter)
        
        # Start the order executor (for fill listening)
        await order_executor.start()
        
        # Submit order through OrderExecutor
        order_result = await order_executor.place_market_order(
            symbol=trade["symbol"],
            qty=trade["quantity"],
            side="BUY",
            trade=trade
        )
        
        print(f"   Order Result: {order_result}")
        
        # 4. Update statuses
        print("\n4. UPDATING STATUSES:")
        trade["order_status"] = "Entry Order Submitted"
        trade["trade_status"] = "Pending"
        trade["order_id"] = order_result["broker_id"]
        
        print(f"   Order Status: {trade['order_status']}")
        print(f"   Trade Status: {trade['trade_status']}")
        print(f"   Order ID: {trade['order_id']}")
        
        # 5. Simulate order fill (in real system, this comes from broker)
        print("\n5. ORDER FILLED (simulated):")
        # In the real system, the OrderExecutor would receive a fill
        # and call trade_manager.mark_trade_filled()
        trade["order_status"] = "Filled"
        trade["trade_status"] = "Live"
        trade["filled_qty"] = trade["quantity"]
        trade["executed_price"] = 155.00
        
        print(f"   Order Status: {trade['order_status']}")
        print(f"   Trade Status: {trade['trade_status']}")
        print(f"   Filled Qty: {trade['filled_qty']}")
        print(f"   Executed Price: ${trade['executed_price']}")
        
        # Stop the order executor
        await order_executor.stop()
        
    else:
        print("\n3. NO ACTION - Entry condition not met")
    
    print("\n=== ARCHITECTURE EXPLANATION ===")
    print("✅ EntryEvaluator: Evaluates conditions")
    print("✅ OrderExecutor: Manages order submission and fills")
    print("✅ StubAdapter: Simulates broker execution")
    print("✅ Trade Status Updates: Happen when fills are received")

if __name__ == "__main__":
    asyncio.run(corrected_trade_demo()) 