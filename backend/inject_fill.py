#!/usr/bin/env python3
"""
Fill injection script - Inject fills directly through OrderExecutor pipeline
This tests the actual codebase by triggering real fill processing
"""

import requests
import json
import time
import sys
from datetime import datetime

class FillInjector:
    """Inject fills through the actual production OrderExecutor pipeline"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_active_orders(self):
        """Get current active orders from OrderExecutor"""
        try:
            response = self.session.get(f"{self.base_url}/debug/active_orders")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get active orders: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ Error getting active orders: {e}")
            return {}
    
    def inject_fill(self, symbol="AAPL", qty=50, price=220.0, broker_id="TEST_001"):
        """
        Inject a fill through the actual OrderExecutor pipeline
        
        Args:
            symbol: Stock symbol
            qty: Quantity filled
            price: Fill price  
            broker_id: Broker order ID
        """
        fill_data = {
            "broker_id": broker_id,
            "symbol": symbol,
            "qty": qty,
            "price": price
        }
        
        print(f"🎯 Injecting fill: {symbol} {qty} shares @ ${price}")
        print(f"   Broker ID: {broker_id}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/inject_fill",
                json=fill_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Fill injection successful!")
                print(f"   Message: {result.get('message')}")
                return True
            else:
                print(f"❌ Fill injection failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error injecting fill: {e}")
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
                print(f"❌ Failed to get trades: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error getting trade status: {e}")
            return None
    
    def test_entry_fill(self, symbol="AAPL"):
        """Test entry fill injection for current trade using real broker IDs"""
        print(f"🔍 Testing entry fill for {symbol}")
        print("=" * 50)
        
        # Get current status
        print("\n📊 Current Status:")
        current = self.get_trade_status(symbol)
        if not current:
            print("❌ No trade found")
            return
            
        trade_status = current.get('trade_status')
        order_status = current.get('order_status')
        print(f"   Trade Status: {trade_status}")
        print(f"   Order Status: {order_status}")
        print(f"   Quantity: {current.get('calculated_quantity')}")
        
        # Get active orders to find real broker ID
        print("\n🔍 Checking Active Orders:")
        active_orders = self.get_active_orders()
        print(f"   Active orders count: {active_orders.get('count', 0)}")
        
        if order_status == 'Entry Order Submitted':
            print("✅ Trade ready for entry fill injection")
            
            # Find matching broker ID from active orders
            broker_id = None
            orders_data = active_orders.get('active_orders', {})
            
            for bid, order_data in orders_data.items():
                trade_data = order_data.get('trade', {})
                if trade_data.get('symbol') == symbol:
                    broker_id = bid
                    print(f"   ✅ Found active order: {broker_id}")
                    break
            
            if not broker_id:
                print(f"   ❌ No active order found for {symbol}")
                print("   This means the order wasn't properly submitted through OrderExecutor")
                print("   Try injecting a tick first to trigger proper entry submission")
                return
            
            # Inject entry fill with real broker ID
            qty = current.get('calculated_quantity', 50)
            price = 220.0  # Entry trigger price
            
            print(f"\n⚡ Injecting entry fill with REAL broker ID:")
            print(f"   Broker ID: {broker_id}")
            print(f"   Symbol: {symbol}")
            print(f"   Quantity: {qty}")
            print(f"   Price: ${price}")
            
            if self.inject_fill(symbol, qty, price, broker_id):
                time.sleep(1)  # Brief delay for processing
                
                # Check updated status
                print("\n📊 Updated Status:")
                updated = self.get_trade_status(symbol)
                if updated:
                    print(f"   Trade Status: {updated.get('trade_status')}")
                    print(f"   Order Status: {updated.get('order_status')}")
                    print(f"   Filled Qty: {updated.get('filled_qty', 'Not set')}")
                    print(f"   Executed Price: ${updated.get('executed_price', 'Not set')}")
                    
                    # Verify transitions
                    if updated.get('trade_status') == 'Filled':
                        print("✅ Trade status correctly updated to 'Filled'")
                    else:
                        print(f"❌ Trade status not updated. Expected 'Filled', got '{updated.get('trade_status')}'")
                    
                    if updated.get('order_status') == 'Contingent Order Working':
                        print("✅ Order status correctly updated to 'Contingent Order Working'")
                    else:
                        print(f"❌ Order status not updated. Expected 'Contingent Order Working', got '{updated.get('order_status')}'")
                    
                    if updated.get('filled_qty') == qty:
                        print("✅ Filled quantity correct")
                    else:
                        print(f"❌ Filled quantity wrong. Expected {qty}, got {updated.get('filled_qty')}")
                    
                    if updated.get('executed_price') == price:
                        print("✅ Executed price correct")
                    else:
                        print(f"❌ Executed price wrong. Expected ${price}, got ${updated.get('executed_price')}")
                    
                    # Check if active orders was cleared
                    post_fill_orders = self.get_active_orders()
                    if broker_id not in post_fill_orders.get('active_orders', {}):
                        print("✅ Active order properly removed after fill")
                    else:
                        print("❌ Active order not removed after fill")
                    
                    print("\n🎯 Trade is now live! Contingent orders are monitoring:")
                    print("   - Stop loss active")
                    print("   - Take profit active")
                    print("   - Trailing stop active")
                else:
                    print("❌ Failed to get updated status")
            else:
                print("❌ Fill injection failed")
        else:
            print(f"❌ Trade not ready for entry fill")
            print(f"   Expected 'Entry Order Submitted', got '{order_status}'")
            print("   Use inject_tick.py to trigger entry first")
    
    def test_exit_fill(self, symbol="AAPL", exit_type="stop"):
        """Test exit fill injection"""
        print(f"🔍 Testing {exit_type} fill for {symbol}")
        print("=" * 50)
        
        current = self.get_trade_status(symbol)
        if current and current.get('trade_status') == 'Filled':
            qty = current.get('filled_qty', 50)
            
            if exit_type == "stop":
                price = 200.0  # Stop loss price
                broker_id = f"STOP_{symbol}_{int(time.time())}"
            elif exit_type == "target":
                price = 250.0  # Take profit price
                broker_id = f"TARGET_{symbol}_{int(time.time())}"
            else:
                price = 210.0  # Trailing stop
                broker_id = f"TRAIL_{symbol}_{int(time.time())}"
            
            print(f"⚡ Injecting {exit_type} fill at ${price}")
            if self.inject_fill(symbol, qty, price, broker_id):
                time.sleep(1)
                
                updated = self.get_trade_status(symbol)
                if updated:
                    print(f"✅ Trade closed with {exit_type}")
                    print(f"   Trade Status: {updated.get('trade_status')}")
                    print(f"   Exit Price: ${updated.get('exit_price', 'Not set')}")
                    print(f"   P&L: ${updated.get('realized_pnl', 'Not calculated')}")
        else:
            print("❌ No live trade found for exit fill")

def main():
    """Main entry point"""
    injector = FillInjector()
    
    if len(sys.argv) == 1:
        # Default: test entry fill
        print("🎯 Default: Testing AAPL entry fill")
        injector.test_entry_fill("AAPL")
    elif len(sys.argv) == 2:
        if sys.argv[1] == "entry":
            injector.test_entry_fill("AAPL")
        elif sys.argv[1] == "stop":
            injector.test_exit_fill("AAPL", "stop")
        elif sys.argv[1] == "target":
            injector.test_exit_fill("AAPL", "target")
        elif sys.argv[1] == "trail":
            injector.test_exit_fill("AAPL", "trail")
        else:
            try:
                price = float(sys.argv[1])
                injector.inject_fill("AAPL", 50, price)
            except ValueError:
                print("❌ Invalid command or price")
    elif len(sys.argv) == 4:
        # Full specification: symbol, qty, price
        symbol = sys.argv[1].upper()
        try:
            qty = int(sys.argv[2])
            price = float(sys.argv[3])
            injector.inject_fill(symbol, qty, price)
        except ValueError:
            print("❌ Invalid quantity or price format")
    else:
        print("Usage:")
        print("  python inject_fill.py                    # Test AAPL entry fill")
        print("  python inject_fill.py entry              # Test entry fill")
        print("  python inject_fill.py stop               # Test stop loss fill")
        print("  python inject_fill.py target             # Test take profit fill")
        print("  python inject_fill.py trail              # Test trailing stop fill")
        print("  python inject_fill.py 220.0              # AAPL fill at $220")
        print("  python inject_fill.py AAPL 50 220.0      # Full specification")

if __name__ == "__main__":
    main()