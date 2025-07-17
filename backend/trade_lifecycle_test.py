#!/usr/bin/env python3
"""
Test showing full trade lifecycle with status updates
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from engine.trade_manager import TradeManager
from engine.adapters.stub_adapter import StubExecutionAdapter
import json
import asyncio

async def test_trade_lifecycle():
    print("Testing full trade lifecycle with status updates...")
    
    # Create stub adapter for testing
    adapter = StubExecutionAdapter()
    
    # Create trade manager
    trade_manager = TradeManager(adapter, config_path="config/test_trade.json")
    
    # Load test trade
    with open('config/test_trade.json', 'r') as f:
        test_data = json.load(f)
    
    trade = test_data['trades'][0]
    print(f"Initial trade status:")
    print(f"  Order Status: {trade.get('order_status')}")
    print(f"  Trade Status: {trade.get('trade_status')}")
    
    # Test entry evaluation with price above threshold
    current_price = 155.00  # Above entry price of 150.00
    print(f"\nTesting entry with price: ${current_price}")
    
    # This should trigger entry and update statuses
    await trade_manager.evaluate_trade_on_tick("AAPL", current_price)
    
    # Check updated trade
    updated_trade = trade_manager.get_trade_details("AAPL")
    if updated_trade:
        print(f"After entry evaluation:")
        print(f"  Order Status: {updated_trade.get('order_status')}")
        print(f"  Trade Status: {updated_trade.get('trade_status')}")
        print(f"  Entry triggered: {updated_trade.get('entry_triggered', False)}")
    else:
        print("Trade not found in manager")

if __name__ == "__main__":
    asyncio.run(test_trade_lifecycle()) 