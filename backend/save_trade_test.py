#!/usr/bin/env python3
"""
Test that actually saves trade to saved_trades.json
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from engine.entry_evaluator import EntryEvaluator
from engine.adapters.stub_adapter import StubExecutionAdapter
import json

def save_trade_test():
    print("=== SAVE TRADE TEST ===")
    print("Testing actual save to saved_trades.json\n")
    
    # 1. Create a simple trade
    test_trade = {
        "symbol": "AAPL",
        "quantity": 100,
        "direction": "Long",
        "order_status": "Working",
        "trade_status": "Pending",
        "entry_rules": [{"primary_source": "PRICE_ABOVE", "condition": ">=", "secondary_source": "Custom", "value": 150.0}],
        "initial_stop_rules": [{"primary_source": "Price", "condition": "<=", "secondary_source": "Custom", "value": 100.0}],
        "trailing_stop_rules": [{"primary_source": "Price", "condition": "<=", "secondary_source": "EMA 8"}],
        "take_profit_rules": [{"primary_source": "Price", "condition": ">=", "secondary_source": "Custom", "value": 200.0}]
    }
    
    print("1. INITIAL TRADE:")
    print(f"   Symbol: {test_trade['symbol']}")
    print(f"   Quantity: {test_trade['quantity']}")
    print(f"   Order Status: {test_trade['order_status']}")
    print(f"   Trade Status: {test_trade['trade_status']}")
    
    # 2. Evaluate entry condition
    print("\n2. EVALUATING ENTRY CONDITION:")
    entry_eval = EntryEvaluator()
    current_price = 155.00  # Above entry price
    
    print(f"   Current Price: ${current_price}")
    entry_triggered = entry_eval.should_trigger_entry(test_trade, current_price)
    print(f"   Entry Triggered: {entry_triggered}")
    
    if entry_triggered:
        # 3. Execute order
        print("\n3. EXECUTING ORDER:")
        
        adapter = StubExecutionAdapter()
        order = {
            "symbol": test_trade["symbol"],
            "side": "BUY",
            "qty": test_trade["quantity"],
            "order_type": "MARKET",
            "tif": "GTC",
            "price": None
        }
        
        import asyncio
        async def submit_order():
            order_id = await adapter.place_order(order)
            return order_id
        
        order_id = asyncio.run(submit_order())
        print(f"   Order ID: {order_id}")
        
        # 4. Update statuses
        print("\n4. UPDATING STATUSES:")
        test_trade["order_status"] = "Entry Order Submitted"
        test_trade["trade_status"] = "Pending"
        test_trade["order_id"] = order_id
        
        print(f"   Order Status: {test_trade['order_status']}")
        print(f"   Trade Status: {test_trade['trade_status']}")
        
        # 5. Simulate order fill
        print("\n5. ORDER FILLED:")
        test_trade["order_status"] = "Filled"
        test_trade["trade_status"] = "Live"
        test_trade["filled_qty"] = test_trade["quantity"]
        test_trade["executed_price"] = 155.00
        
        print(f"   Order Status: {test_trade['order_status']}")
        print(f"   Trade Status: {test_trade['trade_status']}")
        print(f"   Filled Qty: {test_trade['filled_qty']}")
        print(f"   Executed Price: ${test_trade['executed_price']}")
        
        # 6. Save to saved_trades.json
        print("\n6. SAVING TO saved_trades.json:")
        
        # Load existing trades
        config_path = "config/saved_trades.json"
        try:
            with open(config_path, 'r') as f:
                existing_trades = json.load(f)
        except FileNotFoundError:
            existing_trades = []
        
        # Add our trade
        existing_trades.append(test_trade)
        
        # Save back to file
        with open(config_path, 'w') as f:
            json.dump(existing_trades, f, indent=2)
        
        print(f"   Saved {len(existing_trades)} trades to {config_path}")
        print(f"   Latest trade: {test_trade['symbol']} {test_trade['filled_qty']} @ ${test_trade['executed_price']}")
        
    else:
        print("\n3. NO ACTION - Entry condition not met")
    
    print("\n=== TEST COMPLETE ===")
    print("Check config/saved_trades.json to see the updated trade!")

if __name__ == "__main__":
    save_trade_test() 