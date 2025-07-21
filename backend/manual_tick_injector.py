#!/usr/bin/env python3
"""
Manual Tick Injector - Easy discretionary tick injection for testing
Simple interface for manual testing and experimentation
"""

import requests
import json
import time
from datetime import datetime
from typing import Optional

class ManualTickInjector:
    """Simple, flexible tick injector for manual testing"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        print(f"📡 Connected to trading system at {base_url}")
        print("=" * 60)
    
    def inject(self, symbol: str, price: float, volume: int = 100) -> bool:
        """Inject a single tick - main method for manual use"""
        tick_data = {
            "symbol": symbol.upper(),
            "price": price,
            "timestamp": datetime.now().isoformat(),
            "volume": volume,
            "bid": round(price - 0.01, 2),
            "ask": round(price + 0.01, 2)
        }
        
        print(f"🎯 Injecting: {symbol.upper()} @ ${price}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/inject_tick",
                json=tick_data,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✅ Success!")
                self._show_status(symbol)
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def status(self, symbol: Optional[str] = None) -> dict:
        """Get current trade status"""
        try:
            response = self.session.get(f"{self.base_url}/trades")
            if response.status_code == 200:
                trades = response.json()
                
                if symbol:
                    # Find specific symbol
                    for trade in trades:
                        if trade.get("symbol", "").upper() == symbol.upper():
                            return trade
                    print(f"❌ No trades found for {symbol.upper()}")
                    return {}
                else:
                    # Show all trades
                    if trades:
                        print("\n📊 Current Trades:")
                        for trade in trades:
                            sym = trade.get("symbol", "N/A")
                            t_status = trade.get("trade_status", "N/A")
                            o_status = trade.get("order_status", "N/A")
                            print(f"  {sym}: Trade={t_status}, Order={o_status}")
                    else:
                        print("📊 No active trades")
                    return {"all_trades": trades}
            else:
                print(f"❌ Failed to get status: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            return {}
    
    def _show_status(self, symbol: str):
        """Show status after tick injection"""
        trade = self.status(symbol)
        if trade and trade != {}:
            t_status = trade.get("trade_status", "N/A")
            o_status = trade.get("order_status", "N/A")
            print(f"📊 Status: Trade={t_status}, Order={o_status}")
    
    def quick_test(self, symbol: str = "AAPL"):
        """Quick test sequence for a symbol"""
        print(f"\n🧪 Quick test sequence for {symbol.upper()}")
        print("-" * 40)
        
        # Show initial status
        print("Initial status:")
        self.status(symbol)
        
        # Simple test sequence
        test_prices = [215.0, 220.0, 225.0, 250.0]
        
        for price in test_prices:
            print(f"\n⚡ Testing ${price}...")
            self.inject(symbol, price)
            time.sleep(0.5)  # Brief pause
    
    def interactive_mode(self):
        """Interactive mode for manual testing"""
        print("\n🎮 Interactive Mode")
        print("Commands:")
        print("  <symbol> <price>  - Inject tick (e.g., 'AAPL 220.5')")
        print("  status           - Show all trades")
        print("  status <symbol>  - Show specific trade")
        print("  quit             - Exit")
        print("-" * 40)
        
        while True:
            try:
                cmd = input("\n> ").strip()
                if not cmd:
                    continue
                
                if cmd.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if cmd.lower() == 'status':
                    self.status()
                    continue
                
                if cmd.lower().startswith('status '):
                    symbol = cmd[7:].strip()
                    self.status(symbol)
                    continue
                
                # Parse symbol and price
                parts = cmd.split()
                if len(parts) == 2:
                    symbol, price_str = parts
                    try:
                        price = float(price_str)
                        self.inject(symbol, price)
                    except ValueError:
                        print("❌ Invalid price format")
                else:
                    print("❌ Usage: <symbol> <price> (e.g., 'AAPL 220.5')")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main entry point with simple usage"""
    injector = ManualTickInjector()
    
    print("🚀 Manual Tick Injector Ready!")
    print("\nQuick Usage:")
    print("  injector.inject('AAPL', 220.0)    # Inject AAPL at $220")
    print("  injector.status('AAPL')           # Check AAPL status")
    print("  injector.status()                 # Check all trades")
    print("  injector.quick_test('AAPL')       # Run quick test")
    print("  injector.interactive_mode()       # Interactive mode")
    print("\nStarting interactive mode...")
    
    # Start interactive mode
    injector.interactive_mode()

if __name__ == "__main__":
    main()