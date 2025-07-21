"""
Manual Trade Lifecycle Testing Guide
====================================

This script provides step-by-step manual testing of your AAPL trade
with tick injection at each lifecycle phase.

Your Trade Configuration:
- Symbol: AAPL
- Direction: Long
- Quantity: 50 shares
- Entry Trigger: Price >= $220.00
- Stop Loss: Price <= $200.00  
- Take Profit: Price >= $250.00
- Trailing Stop: Price <= SMA(21) ≈ $206.94
- Current Price: $211.18

Test Plan:
==========
1. Activate trade (set to Working/Pending status)
2. Inject tick at $220.00 to trigger entry
3. Simulate entry fill at $220.00
4. Test exit conditions with various price ticks
5. Simulate exit fill and verify closure

"""

import asyncio
import json
import requests
import time
from typing import Dict, Any

class ManualLifecycleTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.symbol = "AAPL"
        self.current_trade = None
        
    def print_header(self, phase: str, description: str):
        """Print formatted phase header"""
        print("\n" + "="*80)
        print(f"📋 {phase}: {description}")
        print("="*80)
    
    def print_trade_status(self, trade: Dict[str, Any]):
        """Print current trade status"""
        print(f"🎯 Symbol: {trade.get('symbol', 'N/A')}")
        print(f"📊 Order Status: {trade.get('order_status', 'N/A')}")
        print(f"📈 Trade Status: {trade.get('trade_status', 'N/A')}")
        print(f"💰 Quantity: {trade.get('quantity', trade.get('calculated_quantity', 'N/A'))}")
        print(f"🏷️ Direction: {trade.get('direction', 'N/A')}")
        
        if trade.get('executed_price'):
            print(f"💵 Entry Price: ${trade.get('executed_price'):.2f}")
        if trade.get('filled_qty'):
            print(f"📦 Filled Qty: {trade.get('filled_qty')}")
        if trade.get('exit_price'):
            print(f"🚪 Exit Price: ${trade.get('exit_price'):.2f}")
        if trade.get('realized_pnl'):
            print(f"💸 P&L: ${trade.get('realized_pnl'):.2f}")
    
    def get_current_trades(self):
        """Fetch current trades from API"""
        try:
            response = requests.get(f"{self.base_url}/trades")
            if response.status_code == 200:
                trades = response.json()
                # Find AAPL trade
                for trade in trades:
                    if trade.get('symbol') == self.symbol:
                        self.current_trade = trade
                        return trade
            return None
        except Exception as e:
            print(f"❌ Error fetching trades: {e}")
            return None
    
    def inject_tick(self, price: float, description: str = ""):
        """Inject a price tick"""
        try:
            tick_data = {
                "symbol": self.symbol,
                "price": price
            }
            
            print(f"\n💉 Injecting Tick: {self.symbol} @ ${price:.2f}")
            if description:
                print(f"📝 Purpose: {description}")
            
            response = requests.post(f"{self.base_url}/inject_tick", json=tick_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result['message']}")
                return True
            else:
                print(f"❌ Tick injection failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error injecting tick: {e}")
            return False
    
    def simulate_entry_fill(self, fill_price: float, filled_qty: int):
        """Simulate entry order fill"""
        try:
            fill_data = {
                "symbol": self.symbol,
                "fill_price": fill_price,
                "filled_qty": filled_qty
            }
            
            print(f"\n🔄 Simulating Entry Fill: {filled_qty} shares @ ${fill_price:.2f}")
            
            response = requests.post(f"{self.base_url}/simulate_entry_fill", json=fill_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result['message']}")
                return True
            else:
                print(f"❌ Entry fill simulation failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error simulating entry fill: {e}")
            return False
    
    def simulate_exit_fill(self, exit_price: float, exit_qty: int):
        """Simulate exit order fill"""
        try:
            fill_data = {
                "symbol": self.symbol,
                "exit_price": exit_price,
                "exit_qty": exit_qty
            }
            
            print(f"\n🔄 Simulating Exit Fill: {exit_qty} shares @ ${exit_price:.2f}")
            
            response = requests.post(f"{self.base_url}/simulate_exit_fill", json=fill_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result['message']}")
                return True
            else:
                print(f"❌ Exit fill simulation failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error simulating exit fill: {e}")
            return False
    
    def activate_trade(self):
        """Activate the trade (this would normally be done via GUI)"""
        print("\n🚀 ACTIVATION STEP:")
        print("1. In the GUI, click 'Activate' on your AAPL trade")
        print("2. This will set order_status='Working' and trade_status='Pending'")
        print("3. Press Enter when ready to continue...")
        input()
    
    def wait_for_input(self, message: str = "Press Enter to continue..."):
        """Wait for user input"""
        print(f"\n⏸️ {message}")
        input()
    
    def run_manual_test(self):
        """Run the complete manual test sequence"""
        print("🚀 MANUAL TRADE LIFECYCLE TEST")
        print(f"Testing Symbol: {self.symbol}")
        print("\nMake sure:")
        print("1. Backend server is running (python -m backend.app)")
        print("2. IB Gateway/TWS is connected")
        print("3. Your AAPL trade is saved in saved_trades.json")
        
        self.wait_for_input("Ready to begin? Press Enter...")
        
        # Phase 1: Initial State
        self.print_header("PHASE 1", "Initial Trade State")
        trade = self.get_current_trades()
        if trade:
            print("📋 Current Trade Configuration:")
            self.print_trade_status(trade)
            
            # Show entry/exit rules
            entry_rules = trade.get('entry_rules', [])
            if entry_rules:
                entry_rule = entry_rules[0]
                print(f"🎯 Entry Rule: {entry_rule['primary_source']} {entry_rule['condition']} {entry_rule['secondary_source']} ({entry_rule['value']})")
            
            stop_rules = trade.get('initial_stop_rules', [])
            if stop_rules:
                stop_rule = stop_rules[0]
                print(f"🛑 Stop Rule: {stop_rule['primary_source']} {stop_rule['condition']} {stop_rule['secondary_source']} ({stop_rule['value']})")
            
            tp_rules = trade.get('take_profit_rules', [])
            if tp_rules:
                tp_rule = tp_rules[0]
                print(f"🎯 Take Profit Rule: {tp_rule['primary_source']} {tp_rule['condition']} {tp_rule['secondary_source']} ({tp_rule['value']})")
        
        self.activate_trade()
        
        # Phase 2: Entry Trigger
        self.print_header("PHASE 2", "Entry Condition Trigger")
        print("💡 Your entry rule triggers when Price >= $220.00")
        print("📈 Current market price is around $211.18")
        print("🎯 We'll inject a tick at $220.00 to trigger entry")
        
        self.wait_for_input("Ready to trigger entry?")
        
        # Inject entry trigger tick
        self.inject_tick(220.00, "Trigger entry condition (Price >= $220.00)")
        
        # Check status after entry trigger
        time.sleep(2)
        trade = self.get_current_trades()
        if trade:
            print("\n📊 Status After Entry Trigger:")
            self.print_trade_status(trade)
            expected_order_status = "Entry Order Submitted"
            if trade.get('order_status') == expected_order_status:
                print(f"✅ Expected status transition occurred: {expected_order_status}")
            else:
                print(f"⚠️ Unexpected status: {trade.get('order_status')} (expected: {expected_order_status})")
        
        self.wait_for_input("Observe the status change, then continue...")
        
        # Phase 3: Entry Fill
        self.print_header("PHASE 3", "Entry Order Fill")
        print("💰 Now we'll simulate the entry order being filled")
        print("📦 Simulating fill: 50 shares @ $220.00")
        
        self.wait_for_input("Ready to simulate entry fill?")
        
        # Simulate entry fill
        self.simulate_entry_fill(220.00, 50)
        
        # Check status after entry fill
        time.sleep(2)
        trade = self.get_current_trades()
        if trade:
            print("\n📊 Status After Entry Fill:")
            self.print_trade_status(trade)
            expected_order_status = "Contingent Order Working"
            expected_trade_status = "Filled"
            if (trade.get('order_status') == expected_order_status and 
                trade.get('trade_status') == expected_trade_status):
                print(f"✅ Expected status transitions occurred")
                print(f"   Order: {expected_order_status}")
                print(f"   Trade: {expected_trade_status}")
            else:
                print(f"⚠️ Status check:")
                print(f"   Order: {trade.get('order_status')} (expected: {expected_order_status})")
                print(f"   Trade: {trade.get('trade_status')} (expected: {expected_trade_status})")
        
        self.wait_for_input("Trade is now LIVE with market risk. Continue to exit testing...")
        
        # Phase 4: Exit Condition Testing
        self.print_header("PHASE 4", "Exit Condition Testing")
        print("🎯 Now let's test the exit conditions:")
        print("   🛑 Stop Loss: Price <= $200.00")
        print("   📈 Take Profit: Price >= $250.00")
        print("   📉 Trailing Stop: Price <= SMA(21) ≈ $206.94")
        
        print("\n🧪 Test Options:")
        print("1. Test Stop Loss (inject tick at $200.00)")
        print("2. Test Take Profit (inject tick at $250.00)")
        print("3. Test Trailing Stop (inject tick at $206.50)")
        
        choice = input("\nEnter choice (1/2/3): ").strip()
        
        if choice == "1":
            # Test Stop Loss
            print("\n🛑 Testing Stop Loss Trigger")
            self.inject_tick(200.00, "Trigger stop loss (Price <= $200.00)")
            exit_price = 200.00
            
        elif choice == "2":
            # Test Take Profit
            print("\n📈 Testing Take Profit Trigger")
            self.inject_tick(250.00, "Trigger take profit (Price >= $250.00)")
            exit_price = 250.00
            
        elif choice == "3":
            # Test Trailing Stop
            print("\n📉 Testing Trailing Stop Trigger")
            self.inject_tick(206.50, "Trigger trailing stop (Price <= SMA(21))")
            exit_price = 206.50
            
        else:
            print("Invalid choice, defaulting to stop loss test")
            self.inject_tick(200.00, "Trigger stop loss (Price <= $200.00)")
            exit_price = 200.00
        
        # Check status after exit trigger
        time.sleep(2)
        trade = self.get_current_trades()
        if trade:
            print("\n📊 Status After Exit Trigger:")
            self.print_trade_status(trade)
            expected_order_status = "Contingent Order Submitted"
            if trade.get('order_status') == expected_order_status:
                print(f"✅ Expected status transition: {expected_order_status}")
            else:
                print(f"⚠️ Status: {trade.get('order_status')} (expected: {expected_order_status})")
        
        self.wait_for_input("Exit order submitted to broker. Ready for exit fill?")
        
        # Phase 5: Exit Fill
        self.print_header("PHASE 5", "Exit Order Fill & Trade Closure")
        print(f"💰 Simulating exit fill at ${exit_price:.2f}")
        
        # Simulate exit fill
        self.simulate_exit_fill(exit_price, 50)
        
        # Check final status
        time.sleep(2)
        trade = self.get_current_trades()
        if trade:
            print("\n📊 Final Trade Status:")
            self.print_trade_status(trade)
            expected_order_status = "Inactive"
            expected_trade_status = "Closed"
            if (trade.get('order_status') == expected_order_status and 
                trade.get('trade_status') == expected_trade_status):
                print(f"✅ Trade successfully closed!")
                print(f"   Final Order Status: {expected_order_status}")
                print(f"   Final Trade Status: {expected_trade_status}")
                
                # Calculate and display P&L
                entry_price = trade.get('executed_price', 220.00)
                pnl = (exit_price - entry_price) * 50  # Long position
                print(f"💸 Calculated P&L: ${pnl:.2f}")
                
                if trade.get('realized_pnl'):
                    print(f"✅ System P&L: ${trade.get('realized_pnl'):.2f}")
            else:
                print(f"⚠️ Final status check:")
                print(f"   Order: {trade.get('order_status')} (expected: {expected_order_status})")
                print(f"   Trade: {trade.get('trade_status')} (expected: {expected_trade_status})")
        
        # Test Complete
        self.print_header("COMPLETE", "Manual Test Finished")
        print("🎉 Manual trade lifecycle test completed!")
        print("\n📋 Summary:")
        print("✅ Phase 1: Initial state reviewed")
        print("✅ Phase 2: Entry condition triggered")
        print("✅ Phase 3: Entry fill simulated")
        print("✅ Phase 4: Exit condition triggered")
        print("✅ Phase 5: Exit fill and closure")
        print("\n🔍 You should have observed all status transitions:")
        print("   Draft → Working → Entry Order Submitted → Contingent Order Working → Contingent Order Submitted → Inactive")
        print("   (blank) → Pending → Filled → Closed")

if __name__ == "__main__":
    tester = ManualLifecycleTester()
    tester.run_manual_test()