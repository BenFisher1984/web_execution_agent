#!/usr/bin/env python3
"""
Fill Simulation Script - Simulate order fills for testing trade lifecycle
"""

import requests
import json
import time
import sys
from datetime import datetime

class FillSimulator:
    """Simulate broker order fills for testing"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def simulate_fill(self, symbol="AAPL", fill_price=220.0, quantity=50):
        """
        Simulate an order fill
        
        Args:
            symbol: Stock symbol
            fill_price: Price at which order was filled
            quantity: Number of shares filled
        """
        fill_data = {
            "symbol": symbol,
            "fill_price": fill_price,
            "filled_qty": quantity,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"Simulating fill: {symbol} - {quantity} shares @ ${fill_price}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/simulate_fill",
                json=fill_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Fill simulation successful!")
                return True
            else:
                print(f"Fill simulation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error simulating fill: {e}")
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
    
    def test_fill_progression(self, symbol="AAPL"):
        """Test the fill progression step by step - handles both entry and exit fills"""
        print(f"Testing fill progression for {symbol}")
        print("=" * 50)
        
        # Step 1: Get current status
        print("\nStep 1: Current Status")
        current = self.get_trade_status(symbol)
        if current:
            trade_status = current.get('trade_status')
            order_status = current.get('order_status')
            print(f"Trade Status: {trade_status}")
            print(f"Order Status: {order_status}")
            
            # Determine what type of fill to simulate based on current status
            if order_status == 'Entry Order Submitted':
                # Entry fill simulation
                print("Ready for ENTRY fill simulation")
                
                print("\nStep 2: Simulating Entry Fill")
                quantity = current.get('calculated_quantity', 50)
                fill_price = 220.0  # Entry trigger price
                
                if self.simulate_entry_fill(symbol, fill_price, quantity):
                    self._display_post_fill_status(symbol, "Entry")
                else:
                    print("Entry fill simulation failed")
                    
            elif order_status == 'Contingent Order Submitted':
                # Exit fill simulation
                print("Ready for EXIT fill simulation")
                
                print("\nStep 2: Simulating Exit Fill")
                quantity = current.get('filled_qty', current.get('calculated_quantity', 50))
                fill_price = 209.0  # Exit price (stop loss)
                
                if self.simulate_exit_fill(symbol, fill_price, quantity):
                    self._display_post_fill_status(symbol, "Exit")
                else:
                    print("Exit fill simulation failed")
                    
            elif order_status == 'Contingent Order Working':
                print("Trade is live - contingent orders are monitoring")
                print("To test exit fill, first trigger stop/take profit with inject_tick.py")
                
            elif order_status == 'Inactive' and trade_status == 'Closed':
                print("Trade is already closed")
                
            else:
                print(f"Unexpected status combination:")
                print(f"   Order Status: {order_status}")
                print(f"   Trade Status: {trade_status}")
                print("   Cannot determine appropriate fill type")
        else:
            print("No trade found")
    
    def simulate_entry_fill(self, symbol="AAPL", fill_price=220.0, quantity=50):
        """Simulate entry order fill"""
        fill_data = {
            "symbol": symbol,
            "fill_price": fill_price,
            "filled_qty": quantity,
            "fill_type": "entry"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/simulate_entry_fill",
                json=fill_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Entry fill simulation successful!")
                return True
            else:
                print(f"Entry fill failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error simulating entry fill: {e}")
            return False
    
    def simulate_exit_fill(self, symbol="AAPL", fill_price=209.0, quantity=50):
        """Simulate exit order fill"""
        fill_data = {
            "symbol": symbol,
            "exit_price": fill_price,
            "exit_qty": quantity,
            "fill_type": "exit"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/simulate_exit_fill",
                json=fill_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Exit fill simulation successful!")
                return True
            else:
                print(f"Exit fill failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error simulating exit fill: {e}")
            return False
    
    def _display_post_fill_status(self, symbol, fill_type):
        """Display status after fill simulation"""
        time.sleep(1)  # Brief delay for processing
        
        print(f"\nStep 3: Post-{fill_type} Fill Status")
        updated = self.get_trade_status(symbol)
        if updated:
            print(f"Trade Status: {updated.get('trade_status')}")
            print(f"Order Status: {updated.get('order_status')}")
            
            if fill_type == "Entry":
                if updated.get('trade_status') == 'Filled':
                    print("Trade status correctly updated to 'Filled'")
                if updated.get('order_status') == 'Contingent Order Working':
                    print("Order status correctly updated to 'Contingent Order Working'")
                
                print(f"Filled Quantity: {updated.get('filled_qty', 'N/A')}")
                print(f"Entry Price: ${updated.get('executed_price', 'N/A')}")
                
                print("\nChild orders are now active and monitoring exit conditions")
                
            elif fill_type == "Exit":
                if updated.get('trade_status') == 'Closed':
                    print("Trade status correctly updated to 'Closed'")
                if updated.get('order_status') == 'Inactive':
                    print("Order status correctly updated to 'Inactive'")
                
                print(f"Exit Quantity: {updated.get('exit_qty', 'N/A')}")
                print(f"Exit Price: ${updated.get('exit_price', 'N/A')}")
                print(f"Realized P&L: ${updated.get('realized_pnl', 'N/A')}")
                
                print("\nTrade lifecycle completed - position closed")
        else:
            print("Failed to get updated status")

def main():
    """Main entry point"""
    simulator = FillSimulator()
    
    if len(sys.argv) == 1:
        # Default: simulate AAPL entry fill
        print("Default: Simulating AAPL entry fill")
        simulator.test_fill_progression("AAPL")
    elif len(sys.argv) == 2:
        if sys.argv[1] == "test":
            # Run progression test
            simulator.test_fill_progression("AAPL")
        else:
            # Single fill simulation
            try:
                price = float(sys.argv[1])
                simulator.simulate_fill("AAPL", price)
            except ValueError:
                print("Invalid price format")
    elif len(sys.argv) == 4:
        # Full specification: symbol, price, quantity
        symbol = sys.argv[1].upper()
        try:
            price = float(sys.argv[2])
            quantity = int(sys.argv[3])
            simulator.simulate_fill(symbol, price, quantity)
        except ValueError:
            print("Invalid price or quantity format")
    else:
        print("Usage:")
        print("  python simulate_fill.py                    # Test AAPL fill progression")
        print("  python simulate_fill.py test               # Same as above")
        print("  python simulate_fill.py 220.0              # AAPL fill at $220")
        print("  python simulate_fill.py AAPL 220.0 50      # Full specification")

if __name__ == "__main__":
    main()