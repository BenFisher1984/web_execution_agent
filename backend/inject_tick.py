#!/usr/bin/env python3
"""
Enhanced tick injection script for comprehensive trade lifecycle testing
"""

import asyncio
import json
import requests
import time
import sys
from datetime import datetime

class TickInjector:
    """Professional tick injection for testing trade lifecycles"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def inject_tick(self, symbol="AAPL", price=220.0):
        """Inject a single tick"""
        tick_data = {
            "symbol": symbol,
            "price": price,
            "timestamp": datetime.now().isoformat(),
            "volume": 100,
            "bid": price - 0.01,
            "ask": price + 0.01
        }
        
        print(f"Injecting tick: {symbol} @ ${price}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/inject_tick",
                json=tick_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Tick injection successful!")
                return True
            else:
                print(f"Tick injection failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error injecting tick: {e}")
            return False
    
    def get_trade_status(self, symbol="AAPL"):
        """Get current trade status"""
        try:
            response = self.session.get(f"{self.base_url}/trades")
            if response.status_code == 200:
                trades = response.json()
                for trade in trades:
                    if trade.get("symbol") == symbol:
                        return trade
                return None
            else:
                print(f"Failed to get trades: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error getting trade status: {e}")
            return None
    
    def run_lifecycle_test(self, symbol="AAPL"):
        """Run complete AAPL lifecycle test"""
        print(f"Starting lifecycle test for {symbol}")
        print("=" * 50)
        
        # AAPL lifecycle test sequence
        test_sequence = [
            {"price": 215.00, "expected": "Still pending (below entry)"},
            {"price": 220.00, "expected": "Entry triggered"},
            {"price": 225.00, "expected": "Position live"},
            {"price": 230.00, "expected": "Position live (profit)"},
            {"price": 250.00, "expected": "Take profit triggered"},
        ]
        
        for i, step in enumerate(test_sequence):
            print(f"\n📊 Step {i+1}: Testing price ${step['price']}")
            print(f"Expected: {step['expected']}")
            
            # Get status before
            before = self.get_trade_status(symbol)
            if before:
                print(f"Before: Trade={before.get('trade_status')}, Order={before.get('order_status')}")
            
            # Inject tick
            if self.inject_tick(symbol, step['price']):
                time.sleep(1)  # Brief delay
                
                # Get status after
                after = self.get_trade_status(symbol)
                if after:
                    print(f"After:  Trade={after.get('trade_status')}, Order={after.get('order_status')}")
                    
                    # Check for changes
                    if before and after:
                        if (before.get('trade_status') != after.get('trade_status') or 
                            before.get('order_status') != after.get('order_status')):
                            print("🔄 STATUS CHANGE DETECTED!")
                
            print("-" * 30)
            
            # Stop if we reach take profit
            if step['price'] >= 250.00:
                print("✅ Take profit level reached - test complete")
                break
        
        print("✅ Lifecycle test completed")

def main():
    """Main entry point"""
    injector = TickInjector()
    
    if len(sys.argv) == 1:
        # Default: trigger AAPL entry
        print("🎯 Default: Triggering AAPL entry at $220")
        injector.inject_tick("AAPL", 220.0)
    elif len(sys.argv) == 2:
        if sys.argv[1] == "lifecycle":
            # Run full lifecycle test
            injector.run_lifecycle_test()
        else:
            # Single price injection
            try:
                price = float(sys.argv[1])
                injector.inject_tick("AAPL", price)
            except ValueError:
                print("❌ Invalid price format")
    elif len(sys.argv) == 3:
        # Symbol and price
        symbol = sys.argv[1].upper()
        try:
            price = float(sys.argv[2])
            injector.inject_tick(symbol, price)
        except ValueError:
            print("❌ Invalid price format")
    else:
        print("Usage:")
        print("  python inject_tick.py                    # Trigger AAPL entry")
        print("  python inject_tick.py lifecycle          # Run full lifecycle test")
        print("  python inject_tick.py 225.0              # AAPL at $225")
        print("  python inject_tick.py AAPL 250.0         # AAPL at $250")

if __name__ == "__main__":
    main() 