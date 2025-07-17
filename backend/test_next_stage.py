#!/usr/bin/env python3
"""
Test that loads the actual trade from saved_trades.json and shows the next stage
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from engine.entry_evaluator import EntryEvaluator
import json

def test_next_stage():
    print("=== TESTING NEXT STAGE OF TRADE LIFECYCLE ===")
    print("Loading actual trade from saved_trades.json\n")
    
    # Load the actual trade from saved_trades.json
    with open('config/saved_trades.json', 'r') as f:
        trades = json.load(f)
    
    trade = trades[0]  # Get the first (and only) trade
    
    print("=== CURRENT TRADE STATE ===")
    print(f"Symbol: {trade['symbol']}")
    print(f"Quantity: {trade['quantity']}")
    print(f"Order Status: {trade['order_status']}")
    print(f"Trade Status: {trade['trade_status']}")
    print(f"Entry Rule: {trade.get('entry_rules', [{}])[0]}")
    print(f"Entry Price: ${trade['entry_rule_price']}")
    print(f"Stop Loss: ${trade['initial_stop_price']}")
    
    # Test entry evaluation with current price
    print("\n=== TESTING ENTRY EVALUATION ===")
    entry_eval = EntryEvaluator()
    
    # Test with price above entry threshold
    current_price = 155.00
    print(f"Current Price: ${current_price}")
    print(f"Entry Threshold: ${trade['entry_rule_price']}")
    
    entry_triggered = entry_eval.should_trigger_entry(trade, current_price)
    print(f"Entry Triggered: {entry_triggered}")
    
    if entry_triggered:
        print("\n=== NEXT STAGE: ENTRY ORDER SHOULD BE SUBMITTED ===")
        print("The system should:")
        print("1. Submit a market order for 100 AAPL")
        print("2. Update order_status to 'Entry Order Submitted'")
        print("3. Keep trade_status as 'Pending'")
        print("4. Generate an order_id")
    else:
        print("\n=== NO ACTION - Entry condition not met ===")
    
    print("\n=== WHAT THE CODE ACTUALLY DOES ===")
    print("The EntryEvaluator.should_trigger_entry() method:")
    print("- Evaluates if current price >= entry threshold")
    print("- Returns True/False")
    print("- Does NOT update trade statuses")
    print("- Does NOT submit orders")
    print("- Does NOT save to file")
    print("\nThe TradeManager would handle the actual order submission and status updates.")

if __name__ == "__main__":
    test_next_stage() 