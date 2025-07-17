#!/usr/bin/env python3
"""
Test script for the new modular architecture.
Tests all evaluators and the parent/child framework.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the modular evaluators
from backend.engine.entry_evaluator import EntryEvaluator
from backend.engine.stop_loss_evaluator import StopLossEvaluator
from backend.engine.take_profit_evaluator import TakeProfitEvaluator
from backend.engine.trailing_stop_evaluator import TrailingStopEvaluator
from backend.engine.portfolio_evaluator import PortfolioEvaluator
from backend.engine.indicators import RollingWindow

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModularArchitectureTester:
    """Test the new modular architecture with a basic trade"""
    
    def __init__(self):
        self.entry_evaluator = EntryEvaluator()
        self.stop_loss_evaluator = StopLossEvaluator()
        self.take_profit_evaluator = TakeProfitEvaluator()
        self.trailing_stop_evaluator = TrailingStopEvaluator()
        self.portfolio_evaluator = PortfolioEvaluator()
        
        # Load test trade
        self.test_trade = self._load_test_trade()
        
        # Create mock rolling window with AAPL price data
        self.rolling_window = self._create_mock_rolling_window()
        
        # Mock portfolio data
        self.portfolio_data = {
            "available_buying_power": 100000,
            "portfolio_value": 100000,
            "current_price": 148.00,
            "positions": {},
            "current_portfolio_loss": 0,
            "max_loss_per_trade": 500.00,
            "max_position_size": 1000,
            "max_concentration": 0.1
        }
    
    def _load_test_trade(self) -> Dict[str, Any]:
        """Load the test trade configuration"""
        try:
            with open("backend/config/test_trade.json", "r") as f:
                data = json.load(f)
                return data["trades"][0]
        except Exception as e:
            logger.error(f"Failed to load test trade: {e}")
            return {}
    
    def _create_mock_rolling_window(self) -> RollingWindow:
        """Create a mock rolling window with AAPL price data"""
        # Simulate AAPL price data around 150
        prices = [145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165]
        rw = RollingWindow(20)
        rw.preload(prices)
        return rw
    
    async def test_entry_evaluator(self):
        """Test the entry evaluator"""
        logger.info("=== Testing Entry Evaluator ===")
        
        # Test 1: Price below entry threshold (should not trigger)
        current_price = 148.00
        should_trigger = self.entry_evaluator.should_trigger_entry(
            self.test_trade, current_price, self.rolling_window
        )
        logger.info(f"Price {current_price}: Should trigger entry = {should_trigger}")
        assert not should_trigger, "Entry should not trigger below threshold"
        
        # Test 2: Price at entry threshold (should trigger)
        current_price = 150.00
        should_trigger = self.entry_evaluator.should_trigger_entry(
            self.test_trade, current_price, self.rolling_window
        )
        logger.info(f"Price {current_price}: Should trigger entry = {should_trigger}")
        assert should_trigger, "Entry should trigger at threshold"
        
        # Test 3: Price above entry threshold (should trigger)
        current_price = 152.00
        should_trigger = self.entry_evaluator.should_trigger_entry(
            self.test_trade, current_price, self.rolling_window
        )
        logger.info(f"Price {current_price}: Should trigger entry = {should_trigger}")
        assert should_trigger, "Entry should trigger above threshold"
        
        logger.info("✅ Entry Evaluator tests passed")
    
    async def test_stop_loss_evaluator(self):
        """Test the stop loss evaluator"""
        logger.info("=== Testing Stop Loss Evaluator ===")
        
        # Debug: Let's see what the dynamic stop calculation produces
        logger.info("Debug: Checking dynamic stop calculation...")
        dynamic_stop = self.stop_loss_evaluator._calculate_dynamic_stop(self.test_trade, self.rolling_window)
        logger.info(f"Debug: Dynamic stop calculated = {dynamic_stop}")
        logger.info(f"Debug: Current price = 148.00")
        logger.info(f"Debug: Static stop = {self.test_trade.get('initial_stop_price')}")
        
        # Test 1: Price above stop (should not trigger)
        current_price = 148.00
        triggered, details = self.stop_loss_evaluator.should_trigger_stop(
            self.test_trade, current_price, self.rolling_window
        )
        logger.info(f"Price {current_price}: Stop triggered = {triggered}")
        logger.info(f"Stop details: {details}")
        assert not triggered, "Stop should not trigger above stop price"
        
        # Test 2: Price at stop (should trigger)
        current_price = 145.00
        triggered, details = self.stop_loss_evaluator.should_trigger_stop(
            self.test_trade, current_price, self.rolling_window
        )
        logger.info(f"Price {current_price}: Stop triggered = {triggered}")
        logger.info(f"Stop details: {details}")
        assert triggered, "Stop should trigger at stop price"
        
        # Test 3: Price below stop (should trigger)
        current_price = 144.00
        triggered, details = self.stop_loss_evaluator.should_trigger_stop(
            self.test_trade, current_price, self.rolling_window
        )
        logger.info(f"Price {current_price}: Stop triggered = {triggered}")
        logger.info(f"Stop details: {details}")
        assert triggered, "Stop should trigger below stop price"
        
        logger.info("✅ Stop Loss Evaluator tests passed")
    
    async def test_take_profit_evaluator(self):
        """Test the take profit evaluator"""
        logger.info("=== Testing Take Profit Evaluator ===")
        
        # Test 1: Price below take profit (should not trigger)
        current_price = 158.00
        triggered, details = self.take_profit_evaluator.should_trigger_take_profit(
            self.test_trade, current_price
        )
        logger.info(f"Price {current_price}: Take profit triggered = {triggered}")
        logger.info(f"Take profit details: {details}")
        assert not triggered, "Take profit should not trigger below target"
        
        # Test 2: Price at first take profit (should trigger)
        current_price = 160.00
        triggered, details = self.take_profit_evaluator.should_trigger_take_profit(
            self.test_trade, current_price
        )
        logger.info(f"Price {current_price}: Take profit triggered = {triggered}")
        logger.info(f"Take profit details: {details}")
        assert triggered, "Take profit should trigger at first target"
        
        # Test 3: Price at second take profit (should trigger both)
        current_price = 165.00
        triggered, details = self.take_profit_evaluator.should_trigger_take_profit(
            self.test_trade, current_price
        )
        logger.info(f"Price {current_price}: Take profit triggered = {triggered}")
        logger.info(f"Take profit details: {details}")
        assert triggered, "Take profit should trigger at second target"
        assert len(details["triggered_targets"]) == 2, "Both targets should be triggered"
        
        logger.info("✅ Take Profit Evaluator tests passed")
    
    async def test_trailing_stop_evaluator(self):
        """Test the trailing stop evaluator"""
        logger.info("=== Testing Trailing Stop Evaluator ===")
        
        # Test 1: Check if trailing stop should be updated
        current_price = 155.00
        should_update, update_details = self.trailing_stop_evaluator.should_update_trailing_stop(
            self.test_trade, current_price, self.rolling_window
        )
        logger.info(f"Price {current_price}: Should update trailing stop = {should_update}")
        logger.info(f"Update details: {update_details}")
        
        # Test 2: Check if trailing stop should be triggered
        current_price = 140.00  # Well below any trailing stop
        triggered, trigger_details = self.trailing_stop_evaluator.should_trigger_trailing_stop(
            self.test_trade, current_price
        )
        logger.info(f"Price {current_price}: Trailing stop triggered = {triggered}")
        logger.info(f"Trigger details: {trigger_details}")
        
        logger.info("✅ Trailing Stop Evaluator tests passed")
    
    async def test_portfolio_evaluator(self):
        """Test the portfolio evaluator"""
        logger.info("=== Testing Portfolio Evaluator ===")
        
        # Test 1: Portfolio should allow trade
        allowed, details = self.portfolio_evaluator.should_allow_trade(
            self.test_trade, self.portfolio_data
        )
        logger.info(f"Portfolio allows trade = {allowed}")
        logger.info(f"Portfolio details: {details}")
        assert allowed, "Portfolio should allow this trade"
        
        # Test 2: Check portfolio details
        portfolio_details = self.portfolio_evaluator.get_portfolio_details(
            self.test_trade, self.portfolio_data
        )
        logger.info(f"Portfolio details: {portfolio_details}")
        
        logger.info("✅ Portfolio Evaluator tests passed")
    
    async def test_parent_child_flow(self):
        """Test the complete parent/child flow"""
        logger.info("=== Testing Parent/Child Flow ===")
        
        # Simulate the complete flow
        current_price = 148.00
        
        # Step 1: Entry evaluation (parent order)
        logger.info(f"Step 1: Evaluating entry at price {current_price}")
        entry_triggered = self.entry_evaluator.should_trigger_entry(
            self.test_trade, current_price, self.rolling_window
        )
        logger.info(f"Entry triggered: {entry_triggered}")
        
        if entry_triggered:
            # Step 2: Portfolio check
            logger.info("Step 2: Portfolio evaluation")
            portfolio_allowed, portfolio_details = self.portfolio_evaluator.should_allow_trade(
                self.test_trade, self.portfolio_data
            )
            logger.info(f"Portfolio allowed: {portfolio_allowed}")
            
            if portfolio_allowed:
                # Step 3: Simulate parent order fill
                logger.info("Step 3: Parent order filled, now evaluating child orders")
                self.test_trade["trade_status"] = "Filled"
                self.test_trade["filled_qty"] = 100
                self.test_trade["executed_price"] = current_price
                
                # Step 4: Evaluate child orders
                logger.info("Step 4: Evaluating child orders")
                
                # Stop loss evaluation
                stop_triggered, stop_details = self.stop_loss_evaluator.should_trigger_stop(
                    self.test_trade, current_price, self.rolling_window
                )
                logger.info(f"Stop loss triggered: {stop_triggered}")
                
                # Take profit evaluation
                tp_triggered, tp_details = self.take_profit_evaluator.should_trigger_take_profit(
                    self.test_trade, current_price
                )
                logger.info(f"Take profit triggered: {tp_triggered}")
                
                # Trailing stop evaluation
                trailing_triggered, trailing_details = self.trailing_stop_evaluator.should_trigger_trailing_stop(
                    self.test_trade, current_price
                )
                logger.info(f"Trailing stop triggered: {trailing_triggered}")
        
        logger.info("✅ Parent/Child Flow test completed")
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting Modular Architecture Tests")
        
        try:
            await self.test_entry_evaluator()
            await self.test_stop_loss_evaluator()
            await self.test_take_profit_evaluator()
            await self.test_trailing_stop_evaluator()
            await self.test_portfolio_evaluator()
            await self.test_parent_child_flow()
            
            logger.info("🎉 All tests passed! Modular architecture is working correctly.")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            raise

async def main():
    """Main test function"""
    tester = ModularArchitectureTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 