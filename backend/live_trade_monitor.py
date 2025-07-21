#!/usr/bin/env python3
"""
Live Trade Monitor - Watch AAPL trade lifecycle with real-time UX updates
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any
import time
from datetime import datetime

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
sys.path.append(parent_dir)

from backend.engine.trade_manager import TradeManager
from backend.engine.order_executor import OrderExecutor
from backend.engine.adapters.stub_adapter import StubExecutionAdapter
from backend.engine.indicators import RollingWindow
from backend.config.status_enums import OrderStatus, TradeStatus

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LiveTradeMonitor:
    """
    Live monitoring of AAPL trade with real-time UX updates
    """
    
    def __init__(self):
        self.stub_adapter = StubExecutionAdapter()
        self.order_executor = OrderExecutor(self.stub_adapter)
        self.trade_manager = TradeManager(
            exec_adapter=self.stub_adapter,
            order_executor=self.order_executor,
            config_path="backend/config/saved_trades.json",
            enable_tasks=False
        )
        
        self.rolling_window = self._create_rolling_window()
        self.current_price = 210.98  # Starting price
        
    def _create_rolling_window(self) -> RollingWindow:
        """Create rolling window with recent AAPL data"""
        rolling_window = RollingWindow(20)
        
        # Add recent price history
        recent_prices = [
            205.50, 206.20, 207.10, 208.00, 208.50,
            209.00, 209.50, 210.00, 210.25, 210.50,
            210.75, 211.00, 210.85, 210.70, 210.60,
            210.45, 210.30, 210.15, 210.00, 210.98
        ]
        
        for price in recent_prices:
            rolling_window.append(price)
        
        return rolling_window
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_header(self):
        """Display monitoring header"""
        print("🍎 AAPL TRADE LIFECYCLE MONITOR")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Current Price: ${self.current_price:.2f}")
        print("=" * 60)
    
    def display_trade_status(self, trade: Dict[str, Any]):
        """Display current trade status in a user-friendly format"""
        print("\n📊 TRADE STATUS")
        print("-" * 30)
        
        # Basic trade info
        print(f"Symbol: {trade.get('symbol', 'N/A')}")
        print(f"Direction: {trade.get('direction', 'N/A')}")
        print(f"Quantity: {trade.get('calculated_quantity', 'N/A')} shares")
        print(f"Position Value: ${trade.get('usd', 'N/A')}")
        
        # Status indicators
        trade_status = trade.get('trade_status', 'Unknown')
        order_status = trade.get('order_status', 'Unknown')
        
        # Color coding for status
        trade_color = self._get_status_color(trade_status)
        order_color = self._get_status_color(order_status)
        
        print(f"Trade Status: {trade_color}{trade_status}\\033[0m")
        print(f"Order Status: {order_color}{order_status}\\033[0m")
        
        # Show filled information if available
        if trade.get('filled_qty'):
            print(f"Filled Quantity: {trade['filled_qty']} shares")
            print(f"Executed Price: ${trade.get('executed_price', 0):.2f}")
        
        # Show P&L if available
        if trade.get('realized_pnl'):
            pnl = trade['realized_pnl']
            pnl_color = "\\033[92m" if pnl >= 0 else "\\033[91m"  # Green for profit, red for loss
            print(f"Realized P&L: {pnl_color}${pnl:.2f}\\033[0m")
    
    def display_rules_status(self, trade: Dict[str, Any]):
        """Display all trading rules and their current status"""
        print("\n📋 TRADING RULES STATUS")
        print("-" * 30)
        
        # Entry Rule
        entry_rules = trade.get('entry_rules', [])
        if entry_rules:
            rule = entry_rules[0]
            target_price = float(rule.get('value', 0))
            condition = rule.get('condition', '')
            
            status = "✅ TRIGGERED" if self._check_condition(self.current_price, condition, target_price) else "⏳ WAITING"
            print(f"Entry Rule: Price {condition} ${target_price:.2f} - {status}")
        
        # Stop Loss Rule
        stop_rules = trade.get('initial_stop_rules', [])
        if stop_rules:
            rule = stop_rules[0]
            target_price = float(rule.get('value', 0))
            condition = rule.get('condition', '')
            
            status = "🛑 TRIGGERED" if self._check_condition(self.current_price, condition, target_price) else "⏳ MONITORING"
            print(f"Stop Loss: Price {condition} ${target_price:.2f} - {status}")
        
        # Take Profit Rule
        tp_rules = trade.get('take_profit_rules', [])
        if tp_rules:
            rule = tp_rules[0]
            target_price = float(rule.get('value', 0))
            condition = rule.get('condition', '')
            
            status = "🎯 TRIGGERED" if self._check_condition(self.current_price, condition, target_price) else "⏳ MONITORING"
            print(f"Take Profit: Price {condition} ${target_price:.2f} - {status}")
        
        # Trailing Stop Rule
        trailing_rules = trade.get('trailing_stop_rules', [])
        if trailing_rules:
            rule = trailing_rules[0]
            current_value = rule.get('value', 0)
            secondary_source = rule.get('secondary_source', '')
            
            if isinstance(current_value, (int, float)):
                target_price = current_value
                condition = rule.get('condition', '')
                status = "🔄 TRIGGERED" if self._check_condition(self.current_price, condition, target_price) else "⏳ MONITORING"
                print(f"Trailing Stop: Price {condition} {secondary_source} (${target_price:.2f}) - {status}")
    
    def _check_condition(self, current_price: float, condition: str, target_price: float) -> bool:
        """Check if price condition is met"""
        if condition == ">=":
            return current_price >= target_price
        elif condition == "<=":
            return current_price <= target_price
        elif condition == ">":
            return current_price > target_price
        elif condition == "<":
            return current_price < target_price
        return False
    
    def _get_status_color(self, status: str) -> str:
        """Get color code for status"""
        status_colors = {
            'Pending': '\\033[93m',      # Yellow
            'Filled': '\\033[92m',       # Green
            'Closed': '\\033[94m',       # Blue
            'Working': '\\033[93m',      # Yellow
            'Entry Order Submitted': '\\033[95m',  # Magenta
            'Contingent Order Working': '\\033[92m',  # Green
            'Inactive': '\\033[90m',     # Gray
        }
        return status_colors.get(status, '\\033[0m')  # Default to no color
    
    def display_next_actions(self, trade: Dict[str, Any]):
        """Display what actions are expected next"""
        print("\n🎯 NEXT EXPECTED ACTIONS")
        print("-" * 30)
        
        trade_status = trade.get('trade_status', '')
        order_status = trade.get('order_status', '')
        
        if trade_status == 'Pending':
            print("⏳ Waiting for entry conditions to be met")
            print("   → Price needs to reach $220.00 or higher")
        elif order_status == 'Entry Order Submitted':
            print("📤 Entry order submitted to broker")
            print("   → Waiting for order fill confirmation")
        elif trade_status == 'Filled':
            print("✅ Position is live - monitoring exit conditions")
            print("   → Stop loss active at $200.00")
            print("   → Take profit active at $250.00")
            print("   → Trailing stop monitoring EMA(8)")
        elif trade_status == 'Closed':
            print("🏁 Trade completed")
            print("   → Position closed and P&L realized")
        else:
            print("❓ Unknown state - check configuration")
    
    def display_controls(self):
        """Display user controls"""
        print("\n🎮 CONTROLS")
        print("-" * 30)
        print("Enter new price to simulate market movement")
        print("Type 'quit' to exit")
        print("Type 'auto' to run automatic scenario")
        print("Type 'reset' to reset trade to initial state")
    
    async def run_live_monitor(self):
        """Run the live monitoring interface"""
        logger.info("🚀 Starting Live Trade Monitor")
        
        # Load AAPL trade
        aapl_trade = None
        for trade in self.trade_manager.trades:
            if trade.get('symbol') == 'AAPL':
                aapl_trade = trade
                break
        
        if not aapl_trade:
            logger.error("AAPL trade not found in configuration")
            return
        
        # Start the monitoring loop
        while True:
            # Clear screen and display current state
            self.clear_screen()
            self.display_header()
            self.display_trade_status(aapl_trade)
            self.display_rules_status(aapl_trade)
            self.display_next_actions(aapl_trade)
            self.display_controls()
            
            # Get user input
            user_input = input("\nEnter command or new price: ").strip()
            
            if user_input.lower() == 'quit':
                print("👋 Exiting monitor...")
                break
            elif user_input.lower() == 'reset':
                # Reset trade to initial state
                aapl_trade['trade_status'] = 'Pending'
                aapl_trade['order_status'] = 'active'
                aapl_trade.pop('filled_qty', None)
                aapl_trade.pop('executed_price', None)
                aapl_trade.pop('realized_pnl', None)
                print("🔄 Trade reset to initial state")
                time.sleep(1)
                continue
            elif user_input.lower() == 'auto':
                await self._run_auto_scenario(aapl_trade)
                continue
            
            # Try to parse as price
            try:
                new_price = float(user_input)
                if new_price <= 0:
                    print("❌ Invalid price. Please enter a positive number.")
                    time.sleep(1)
                    continue
                
                print(f"🔍 DEBUG: Processing price input: {new_price}")
                
                # Update current price
                old_price = self.current_price
                self.current_price = new_price
                print(f"🔍 DEBUG: Updated current_price: {old_price} → {self.current_price}")
                
                # Add to rolling window
                self.rolling_window.append(new_price)
                print(f"🔍 DEBUG: Added price to rolling window, window size: {len(self.rolling_window)}")
                
                # Check if trade exists
                if not aapl_trade:
                    print("❌ DEBUG: No AAPL trade found!")
                    time.sleep(2)
                    continue
                
                print(f"🔍 DEBUG: Trade before evaluation - Status: {aapl_trade.get('trade_status')}, Order: {aapl_trade.get('order_status')}")
                
                # Evaluate trade
                await self.trade_manager.evaluate_trade_on_tick(
                    symbol="AAPL",
                    price=new_price,
                    rolling_window=self.rolling_window
                )
                
                print(f"🔍 DEBUG: Trade after evaluation - Status: {aapl_trade.get('trade_status')}, Order: {aapl_trade.get('order_status')}")
                
                # Show price change
                change = new_price - old_price
                change_color = "\\033[92m" if change >= 0 else "\\033[91m"
                print(f"📈 Price updated: ${old_price:.2f} → ${new_price:.2f} "
                      f"({change_color}{change:+.2f}\\033[0m)")
                
                time.sleep(3)  # Give more time to read debug info
                
            except ValueError:
                print("❌ Invalid input. Please enter a valid price or command.")
                time.sleep(1)
    
    async def _run_auto_scenario(self, trade: Dict[str, Any]):
        """Run automatic price scenario"""
        print("🤖 Running automatic scenario...")
        
        # Entry scenario: move price from current to trigger entry
        scenario_prices = [215.00, 218.00, 220.00, 222.00, 225.00, 
                          230.00, 235.00, 240.00, 245.00, 250.00]
        
        for price in scenario_prices:
            self.current_price = price
            self.rolling_window.append(price)
            
            await self.trade_manager.evaluate_trade_on_tick(
                symbol="AAPL",
                price=price,
                rolling_window=self.rolling_window
            )
            
            print(f"🎯 Auto: Price → ${price:.2f}")
            time.sleep(0.5)
        
        input("Press Enter to continue...")

async def main():
    """Main entry point"""
    monitor = LiveTradeMonitor()
    await monitor.run_live_monitor()

if __name__ == "__main__":
    asyncio.run(main())