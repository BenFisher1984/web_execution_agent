#!/usr/bin/env python3
"""
Focused test for entry rule evaluation only
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from engine.entry_evaluator import EntryEvaluator
import json

def test_entry_only():
    print("Testing entry rule evaluation only...")
    
    # Load test trade
    with open('config/test_trade.json', 'r') as f:
        test_data = json.load(f)
    
    trade = test_data['trades'][0]
    print(f"Loaded trade: {trade['symbol']} {trade['quantity']} shares")
    print(f"Entry rule: {trade.get('entry_rules', [{}])[0]}")
    print(f"Entry price: ${trade.get('entry_rules', [{}])[0].get('price')}")
    
    # Create entry evaluator
    entry_eval = EntryEvaluator()
    
    # Test entry evaluation with price above threshold
    current_price = 155.00  # Above entry price of 150.00
    print(f"\nTesting with price: ${current_price}")
    
    entry_result = entry_eval.should_trigger_entry(trade, current_price)
    print(f"Entry triggered: {entry_result}")
    
    # Test entry evaluation with price below threshold
    current_price = 145.00  # Below entry price of 150.00
    print(f"\nTesting with price: ${current_price}")
    
    entry_result = entry_eval.should_trigger_entry(trade, current_price)
    print(f"Entry triggered: {entry_result}")
    
    print("\nEntry rule test completed!")

if __name__ == "__main__":
    test_entry_only() 