#!/usr/bin/env python3
"""
Test: Buy 100 AAPL if price >= 150, if filled place stop at 140
Shows order and trade status at each stage
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from engine.entry_evaluator import EntryEvaluator
from engine.stop_loss_evaluator import StopLossEvaluator
from engine.adapters.stub_adapter import StubExecutionAdapter
import json

def test_with_stop_loss():
    print("=== TEST WITH STOP LOSS ===")
    print("Buy 100 AAPL if price >= 150, if filled place stop at 140\n")
    
    # 1. Create trade with stop loss
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
    
    print("=== STAGE 1: INITIAL TRADE ===")
    print(f"Symbol: {test_trade['symbol']}")
    print(f"Quantity: {test_trade['quantity']}")
    print(f"Entry Rule: {test_trade['entry_rules']}")
    print(f"Entry Price: ${test_trade['entry_rules'][0]['value']}")
    print(f"Stop Loss: ${test_trade['initial_stop_rules'][0]['value']}")
    print(f"Order Status: {test_trade['order_status']}")
    print(f"Trade Status: {test_trade['trade_status']}")
    
    # 2. Evaluate entry condition
    print("\n=== STAGE 2: ENTRY EVALUATION ===")
    entry_eval = EntryEvaluator()
    current_price = 155.00  # Above entry price
    
    print(f"Current Price: ${current_price}")
    entry_triggered = entry_eval.should_trigger_entry(test_trade, current_price)
    print(f"Entry Triggered: {entry_triggered}")
    
    if entry_triggered:
        # 3. Execute entry order
        print("\n=== STAGE 3: ENTRY ORDER EXECUTION ===")
        
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
        print(f"Order ID: {order_id}")
        print(f"Order: {order['qty']} {order['symbol']} @ market")
        
        # Update status after order submission
        test_trade["order_status"] = "Entry Order Submitted"
        test_trade["trade_status"] = "Pending"
        test_trade["order_id"] = order_id
        
        print(f"Order Status: {test_trade['order_status']}")
        print(f"Trade Status: {test_trade['trade_status']}")
        
        # 4. Simulate order fill
        print("\n=== STAGE 4: ORDER FILLED ===")
        test_trade["order_status"] = "Filled"
        test_trade["trade_status"] = "Live"
        test_trade["filled_qty"] = test_trade["quantity"]
        test_trade["executed_price"] = 155.00
        
        print(f"Order Status: {test_trade['order_status']}")
        print(f"Trade Status: {test_trade['trade_status']}")
        print(f"Filled Qty: {test_trade['filled_qty']}")
        print(f"Executed Price: ${test_trade['executed_price']}")
        
        # 5. Test stop loss evaluation (price above stop)
        print("\n=== STAGE 5: STOP LOSS EVALUATION (Price Above Stop) ===")
        stop_eval = StopLossEvaluator()
        current_price = 145.00  # Above stop price of 140
        
        print(f"Current Price: ${current_price}")
        print(f"Stop Price: ${test_trade['initial_stop_rules'][0]['value']}")
        
        stop_triggered, stop_details = stop_eval.should_trigger_stop(test_trade, current_price)
        print(f"Stop Triggered: {stop_triggered}")
        print(f"Stop Details: {stop_details}")
        
        # 6. Test stop loss evaluation (price below stop)
        print("\n=== STAGE 6: STOP LOSS EVALUATION (Price Below Stop) ===")
        current_price = 135.00  # Below stop price of 140
        
        print(f"Current Price: ${current_price}")
        print(f"Stop Price: ${test_trade['initial_stop_rules'][0]['value']}")
        
        stop_triggered, stop_details = stop_eval.should_trigger_stop(test_trade, current_price)
        print(f"Stop Triggered: {stop_triggered}")
        print(f"Stop Details: {stop_details}")
        
        if stop_triggered:
            # 7. Execute stop loss order
            print("\n=== STAGE 7: STOP LOSS ORDER EXECUTION ===")
            
            stop_order = {
                "symbol": test_trade["symbol"],
                "side": "SELL",  # Sell to close long position
                "qty": test_trade["filled_qty"],
                "order_type": "MARKET",
                "tif": "GTC",
                "price": None
            }
            
            async def submit_stop_order():
                stop_order_id = await adapter.place_order(stop_order)
                return stop_order_id
            
            stop_order_id = asyncio.run(submit_stop_order())
            print(f"Stop Order ID: {stop_order_id}")
            print(f"Stop Order: {stop_order['qty']} {stop_order['symbol']} @ market")
            
            # Update status after stop order submission
            test_trade["order_status"] = "Stop Loss Order Submitted"
            test_trade["trade_status"] = "Live"  # Still live until stop order fills
            test_trade["stop_order_id"] = stop_order_id
            
            print(f"Order Status: {test_trade['order_status']}")
            print(f"Trade Status: {test_trade['trade_status']}")
            
            # 8. Simulate stop order fill
            print("\n=== STAGE 8: STOP LOSS ORDER FILLED ===")
            test_trade["order_status"] = "Filled"
            test_trade["trade_status"] = "Closed"  # Correct status when trade is closed
            test_trade["exit_price"] = 135.00
            test_trade["exit_qty"] = test_trade["filled_qty"]
            
            print(f"Order Status: {test_trade['order_status']}")
            print(f"Trade Status: {test_trade['trade_status']}")
            print(f"Exit Price: ${test_trade['exit_price']}")
            print(f"Exit Qty: {test_trade['exit_qty']}")
            print(f"P&L: ${(test_trade['exit_price'] - test_trade['executed_price']) * test_trade['exit_qty']:.2f}")
        
        # 9. Save to saved_trades.json
        print("\n=== STAGE 9: SAVING TO FILE ===")
        
        config_path = "config/saved_trades.json"
        try:
            with open(config_path, 'r') as f:
                existing_trades = json.load(f)
        except FileNotFoundError:
            existing_trades = []
        
        existing_trades.append(test_trade)
        
        with open(config_path, 'w') as f:
            json.dump(existing_trades, f, indent=2)
        
        print(f"Saved {len(existing_trades)} trades to {config_path}")
        print(f"Latest trade: {test_trade['symbol']} {test_trade['filled_qty']} @ ${test_trade['executed_price']}")
        
    else:
        print("\n=== NO ACTION - Entry condition not met ===")
    
    print("\n=== TRADE LIFECYCLE COMPLETE ===")
    print("Showed order and trade status at each stage!")

if __name__ == "__main__":
    test_with_stop_loss() 