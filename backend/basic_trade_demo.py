#!/usr/bin/env python3
"""
Basic trade demo: Evaluate → Execute → Update Status
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from engine.entry_evaluator import EntryEvaluator
from engine.adapters.stub_adapter import StubExecutionAdapter
import json

def basic_trade_demo():
    print("=== BASIC TRADE DEMO ===")
    print("Goal: Evaluate → Execute → Update Status\n")
    
    # 1. Create a simple trade
    trade = {
        "symbol": "AAPL",
        "quantity": 100,
        "direction": "Long",
        "order_status": "Working",
        "trade_status": "Pending",
        "entry_rules": [{"type": "PRICE_ABOVE", "price": 150.00}],
        "initial_stop_rules": [{"type": "PRICE_BELOW", "price": 140.00}],
        "trailing_stop_rules": [{"type": "PRICE_BELOW", "price": 145.00}],
        "take_profit_rules": [{"type": "PRICE_ABOVE", "price": 160.00}]
    }
    
    print("1. INITIAL TRADE:")
    print(f"   Symbol: {trade['symbol']}")
    print(f"   Quantity: {trade['quantity']}")
    print(f"   Order Status: {trade['order_status']}")
    print(f"   Trade Status: {trade['trade_status']}")
    print(f"   Entry Rule: {trade.get('entry_rules', [{}])[0]}")
    print(f"   Entry Price: ${trade.get('entry_rules', [{}])[0]['price']}")
    
    # 2. Evaluate entry condition
    print("\n2. EVALUATING ENTRY CONDITION:")
    entry_eval = EntryEvaluator()
    current_price = 155.00  # Above entry price
    
    print(f"   Current Price: ${current_price}")
    entry_triggered = entry_eval.should_trigger_entry(trade, current_price)
    print(f"   Entry Triggered: {entry_triggered}")
    
    if entry_triggered:
        # 3. Execute order
        print("\n3. EXECUTING ORDER:")
        adapter = StubExecutionAdapter()
        
        # Create order
        order = {
            "symbol": trade["symbol"],
            "side": "buy",
            "qty": trade["quantity"],
            "order_type": "market",
            "tif": "day",
            "price": None
        }
        
        print(f"   Submitting order: {order['qty']} {order['symbol']} @ market")
        
        # Submit order (this would be async in real code, but we'll simulate)
        import asyncio
        async def submit_order():
            order_id = await adapter.execute_order(order)
            return order_id
        
        order_id = asyncio.run(submit_order())
        print(f"   Order ID: {order_id}")
        
        # 4. Update statuses
        print("\n4. UPDATING STATUSES:")
        trade["order_status"] = "Entry Order Submitted"
        trade["trade_status"] = "Pending"
        trade["order_id"] = order_id
        
        print(f"   Order Status: {trade['order_status']}")
        print(f"   Trade Status: {trade['trade_status']}")
        
        # 5. Simulate order fill
        print("\n5. ORDER FILLED:")
        trade["order_status"] = "Filled"
        trade["trade_status"] = "Live"
        trade["filled_qty"] = trade["quantity"]
        trade["executed_price"] = 155.00
        
        print(f"   Order Status: {trade['order_status']}")
        print(f"   Trade Status: {trade['trade_status']}")
        print(f"   Filled Qty: {trade['filled_qty']}")
        print(f"   Executed Price: ${trade['executed_price']}")
        
    else:
        print("\n3. NO ACTION - Entry condition not met")
    
    print("\n=== DEMO COMPLETE ===")
    print("This shows the basic flow:")
    print("1. Evaluate condition ✅")
    print("2. Execute order ✅") 
    print("3. Update statuses ✅")

if __name__ == "__main__":
    basic_trade_demo() 