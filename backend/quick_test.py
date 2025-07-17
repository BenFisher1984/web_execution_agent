#!/usr/bin/env python3
"""
Quick test script to validate trade evaluation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from engine.trade_manager import TradeManager
from engine.entry_evaluator import EntryEvaluator
from engine.stop_loss_evaluator import StopLossEvaluator
from engine.take_profit_evaluator import TakeProfitEvaluator
from engine.portfolio_evaluator import PortfolioEvaluator
import json

def quick_test():
    print("Starting quick test...")
    
    # Load test trade
    with open('config/test_trade.json', 'r') as f:
        test_data = json.load(f)
    
    trade = test_data['trades'][0]
    print(f"Loaded trade: {trade['symbol']} {trade['quantity']} shares")
    
    # Create evaluators
    entry_eval = EntryEvaluator()
    stop_eval = StopLossEvaluator()
    profit_eval = TakeProfitEvaluator()
    portfolio_eval = PortfolioEvaluator()
    
    # Test entry evaluation
    current_price = 155.00  # Above entry price
    print(f"\nTesting entry evaluation with price: ${current_price}")
    
    entry_result = entry_eval.should_trigger_entry(trade, current_price)
    print(f"Entry evaluation result: {entry_result}")
    
    # Test stop loss evaluation
    current_price = 144.00  # Below stop price
    print(f"\nTesting stop loss evaluation with price: ${current_price}")
    
    stop_result = stop_eval.should_trigger_stop(trade, current_price)
    print(f"Stop loss evaluation result: {stop_result}")
    
    # Test take profit evaluation
    current_price = 161.00  # Above take profit
    print(f"\nTesting take profit evaluation with price: ${current_price}")
    
    profit_result = profit_eval.should_trigger_take_profit(trade, current_price)
    print(f"Take profit evaluation result: {profit_result}")
    
    print("\nQuick test completed successfully!")

if __name__ == "__main__":
    quick_test() 