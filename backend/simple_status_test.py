#!/usr/bin/env python3
"""
Simple test showing why statuses aren't updating
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from engine.entry_evaluator import EntryEvaluator
import json

def test_status_issue():
    print("Testing why statuses aren't updating...")
    
    # Load test trade
    with open('config/test_trade.json', 'r') as f:
        test_data = json.load(f)
    
    trade = test_data['trades'][0]
    print(f"Initial trade:")
    print(f"  Order Status: {trade.get('order_status')}")
    print(f"  Trade Status: {trade.get('trade_status')}")
    print(f"  Entry Rule: {trade.get('entry_rules', [{}])[0]}")
    print(f"  Entry Price: ${trade.get('entry_rule_price')}")
    
    # Create entry evaluator
    entry_eval = EntryEvaluator()
    
    # Test entry evaluation
    current_price = 155.00  # Above entry price
    print(f"\nTesting entry with price: ${current_price}")
    
    entry_result = entry_eval.should_trigger_entry(trade, current_price)
    print(f"Entry triggered: {entry_result}")
    
    print(f"\nAfter entry evaluation:")
    print(f"  Order Status: {trade.get('order_status')} (unchanged)")
    print(f"  Trade Status: {trade.get('trade_status')} (unchanged)")
    
    print("\n=== EXPLANATION ===")
    print("The EntryEvaluator ONLY determines if entry conditions are met.")
    print("It does NOT update trade statuses - that's the TradeManager's job.")
    print("\nTo actually update statuses, you need:")
    print("1. TradeManager to orchestrate the evaluation")
    print("2. OrderExecutor to submit orders")
    print("3. Status updates when orders are filled")
    print("\nThe EntryEvaluator is just one component in the chain!")

if __name__ == "__main__":
    test_status_issue() 