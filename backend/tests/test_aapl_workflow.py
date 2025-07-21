#!/usr/bin/env python3
"""
Comprehensive AAPL Trade Workflow Testing Framework
Tests the complete parent/child lifecycle using the saved AAPL trade configuration.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any, List
import copy

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.engine.trade_manager import TradeManager
from backend.engine.order_executor import OrderExecutor
from backend.engine.adapters.stub_adapter import StubAdapter
from backend.engine.indicators import RollingWindow
from backend.config.status_enums import OrderStatus, TradeStatus

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AAPLWorkflowTester:
    """
    Comprehensive testing framework for AAPL trade workflow.
    Tests all lifecycle stages with realistic price scenarios.
    """
    
    def __init__(self):
        self.stub_adapter = StubAdapter()
        self.order_executor = OrderExecutor(self.stub_adapter)
        self.trade_manager = TradeManager(
            exec_adapter=self.stub_adapter,
            order_executor=self.order_executor,
            config_path="backend/config/saved_trades.json",
            enable_tasks=False
        )
        
        # Load the actual AAPL trade
        self.aapl_trade = self._load_aapl_trade()
        self.rolling_window = self._create_mock_rolling_window()
        
        # Test scenarios
        self.test_scenarios = self._create_test_scenarios()
        
    def _load_aapl_trade(self) -> Dict[str, Any]:
        """Load the AAPL trade from saved_trades.json"""
        try:
            with open("backend/config/saved_trades.json", "r") as f:
                trades = json.load(f)
            
            aapl_trade = None
            for trade in trades:
                if trade.get("symbol") == "AAPL":
                    aapl_trade = trade
                    break
            
            if not aapl_trade:
                raise ValueError("AAPL trade not found in saved_trades.json")
            
            logger.info(f"Loaded AAPL trade: {aapl_trade['symbol']} - {aapl_trade['direction']}")
            return aapl_trade
            
        except Exception as e:
            logger.error(f"Failed to load AAPL trade: {e}")
            raise
    
    def _create_mock_rolling_window(self) -> RollingWindow:
        """Create rolling window with realistic AAPL price data"""
        rolling_window = RollingWindow(20)
        
        # Historical AAPL prices leading up to current price (210.98)
        historical_prices = [
            205.50, 206.20, 207.10, 208.00, 208.50,
            209.00, 209.50, 210.00, 210.25, 210.50,
            210.75, 211.00, 210.85, 210.70, 210.60,
            210.45, 210.30, 210.15, 210.00, 210.98
        ]
        
        for price in historical_prices:
            rolling_window.add_price(price)
        
        return rolling_window
    
    def _create_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create comprehensive test scenarios for each lifecycle stage"""
        return [
            # Scenario 1: Entry Trigger Test
            {
                "name": "Entry Trigger - Price >= $220",
                "stage": "entry",
                "price_sequence": [218.00, 219.50, 220.00, 220.50],
                "expected_transitions": [
                    {"trade_status": "Pending", "order_status": "Working"},
                    {"trade_status": "Pending", "order_status": "Working"},
                    {"trade_status": "Pending", "order_status": "Entry Order Submitted"},
                    {"trade_status": "Filled", "order_status": "Contingent Order Working"}
                ]
            },
            
            # Scenario 2: Stop Loss Trigger Test
            {
                "name": "Stop Loss Trigger - Price <= $200",
                "stage": "stop_loss",
                "initial_state": {"trade_status": "Filled", "order_status": "Contingent Order Working"},
                "price_sequence": [210.00, 205.00, 200.00, 195.00],
                "expected_transitions": [
                    {"trade_status": "Filled", "order_status": "Contingent Order Working"},
                    {"trade_status": "Filled", "order_status": "Contingent Order Working"},
                    {"trade_status": "Filled", "order_status": "Contingent Order Submitted"},
                    {"trade_status": "Closed", "order_status": "Inactive"}
                ]
            },
            
            # Scenario 3: Take Profit Trigger Test
            {
                "name": "Take Profit Trigger - Price >= $250",
                "stage": "take_profit",
                "initial_state": {"trade_status": "Filled", "order_status": "Contingent Order Working"},
                "price_sequence": [240.00, 245.00, 250.00, 255.00],
                "expected_transitions": [
                    {"trade_status": "Filled", "order_status": "Contingent Order Working"},
                    {"trade_status": "Filled", "order_status": "Contingent Order Working"},
                    {"trade_status": "Filled", "order_status": "Contingent Order Submitted"},
                    {"trade_status": "Closed", "order_status": "Inactive"}
                ]
            },
            
            # Scenario 4: Trailing Stop Test
            {
                "name": "Trailing Stop Test - EMA(8) Dynamic",
                "stage": "trailing_stop",
                "initial_state": {"trade_status": "Filled", "order_status": "Contingent Order Working"},
                "price_sequence": [225.00, 230.00, 235.00, 220.00],  # Rise then fall
                "expected_behavior": "trailing_stop_updates_then_triggers"
            },
            
            # Scenario 5: Complete Lifecycle Test
            {
                "name": "Complete Lifecycle - Entry to Exit",
                "stage": "complete",
                "price_sequence": [
                    # Entry phase
                    218.00, 219.50, 220.00, 220.50,
                    # Live trading phase
                    225.00, 230.00, 235.00, 240.00,
                    # Exit phase (trailing stop trigger)
                    235.00, 230.00, 225.00, 220.00
                ],
                "expected_phases": ["entry", "live_trading", "exit"]
            }
        ]
    
    async def run_comprehensive_tests(self):
        """Run all test scenarios"""
        logger.info("🚀 Starting AAPL Workflow Comprehensive Testing")
        logger.info("="*60)
        
        test_results = []
        
        for scenario in self.test_scenarios:
            logger.info(f"\n📊 Running Scenario: {scenario['name']}")
            logger.info("-" * 50)
            
            try:
                result = await self._run_scenario(scenario)
                test_results.append(result)
                
                if result["success"]:
                    logger.info(f"✅ {scenario['name']} - PASSED")
                else:
                    logger.error(f"❌ {scenario['name']} - FAILED: {result['error']}")
                    
            except Exception as e:
                logger.error(f"💥 {scenario['name']} - EXCEPTION: {e}")
                test_results.append({
                    "scenario": scenario["name"],
                    "success": False,
                    "error": str(e)
                })
        
        # Summary report
        self._generate_test_report(test_results)
        
        return test_results
    
    async def _run_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run individual test scenario"""
        trade_copy = copy.deepcopy(self.aapl_trade)
        
        # Set initial state if specified
        if "initial_state" in scenario:
            trade_copy.update(scenario["initial_state"])
        
        # Update trade manager with test trade
        self.trade_manager.trades = [trade_copy]
        self.trade_manager.trade_index = {trade_copy["symbol"]: trade_copy}
        
        status_transitions = []
        
        for i, price in enumerate(scenario["price_sequence"]):
            # Update rolling window
            self.rolling_window.add_price(price)
            
            # Capture status before evaluation
            before_trade_status = trade_copy.get("trade_status")
            before_order_status = trade_copy.get("order_status")
            
            # Evaluate trade on tick
            await self.trade_manager.evaluate_trade_on_tick(
                symbol="AAPL",
                price=price,
                rolling_window=self.rolling_window
            )
            
            # Capture status after evaluation
            after_trade_status = trade_copy.get("trade_status")
            after_order_status = trade_copy.get("order_status")
            
            # Record transition
            transition = {
                "step": i,
                "price": price,
                "before": {
                    "trade_status": before_trade_status,
                    "order_status": before_order_status
                },
                "after": {
                    "trade_status": after_trade_status,
                    "order_status": after_order_status
                },
                "changed": (before_trade_status != after_trade_status or 
                          before_order_status != after_order_status)
            }
            
            status_transitions.append(transition)
            
            logger.info(f"  Step {i}: Price=${price:.2f} | "
                       f"Trade: {before_trade_status} → {after_trade_status} | "
                       f"Order: {before_order_status} → {after_order_status}")
        
        # Validate results
        success = self._validate_scenario_results(scenario, status_transitions)
        
        return {
            "scenario": scenario["name"],
            "success": success,
            "transitions": status_transitions,
            "final_state": {
                "trade_status": trade_copy.get("trade_status"),
                "order_status": trade_copy.get("order_status")
            }
        }
    
    def _validate_scenario_results(self, scenario: Dict[str, Any], 
                                 transitions: List[Dict[str, Any]]) -> bool:
        """Validate scenario results against expected outcomes"""
        if "expected_transitions" in scenario:
            expected = scenario["expected_transitions"]
            if len(transitions) != len(expected):
                return False
            
            for i, (actual, expected_state) in enumerate(zip(transitions, expected)):
                actual_after = actual["after"]
                if (actual_after["trade_status"] != expected_state["trade_status"] or
                    actual_after["order_status"] != expected_state["order_status"]):
                    logger.error(f"Step {i}: Expected {expected_state}, got {actual_after}")
                    return False
        
        return True
    
    def _generate_test_report(self, results: List[Dict[str, Any]]):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*60)
        logger.info("📋 AAPL WORKFLOW TEST REPORT")
        logger.info("="*60)
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.info("\n🔍 FAILED TESTS:")
            for result in results:
                if not result["success"]:
                    logger.info(f"  - {result['scenario']}: {result.get('error', 'Unknown error')}")
        
        logger.info("\n" + "="*60)
    
    async def run_single_scenario(self, scenario_name: str):
        """Run a single test scenario by name"""
        scenario = next((s for s in self.test_scenarios if s["name"] == scenario_name), None)
        if not scenario:
            logger.error(f"Scenario '{scenario_name}' not found")
            return None
        
        logger.info(f"🎯 Running Single Scenario: {scenario_name}")
        return await self._run_scenario(scenario)
    
    async def run_debug_mode(self):
        """Run tests in debug mode with detailed output"""
        logger.info("🔍 Debug Mode - Step-by-step execution")
        
        # Start with entry trigger scenario
        scenario = self.test_scenarios[0]  # Entry trigger
        
        trade_copy = copy.deepcopy(self.aapl_trade)
        self.trade_manager.trades = [trade_copy]
        self.trade_manager.trade_index = {trade_copy["symbol"]: trade_copy}
        
        logger.info(f"Initial State: {trade_copy}")
        
        for i, price in enumerate(scenario["price_sequence"]):
            input(f"\nPress Enter to test price ${price:.2f} (step {i+1})...")
            
            # Show detailed state before
            logger.info(f"BEFORE - Trade Status: {trade_copy.get('trade_status')}, "
                       f"Order Status: {trade_copy.get('order_status')}")
            
            # Update rolling window
            self.rolling_window.add_price(price)
            
            # Evaluate
            await self.trade_manager.evaluate_trade_on_tick(
                symbol="AAPL",
                price=price,
                rolling_window=self.rolling_window
            )
            
            # Show detailed state after
            logger.info(f"AFTER  - Trade Status: {trade_copy.get('trade_status')}, "
                       f"Order Status: {trade_copy.get('order_status')}")
            
            # Show evaluator states
            logger.info(f"Entry Details: {self.trade_manager.entry_evaluator.get_entry_details(trade_copy)}")
            logger.info(f"Stop Details: {self.trade_manager.stop_loss_evaluator.get_stop_details(trade_copy)}")

async def main():
    """Main test runner"""
    tester = AAPLWorkflowTester()
    
    # Choose test mode
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "debug":
            await tester.run_debug_mode()
        elif mode == "single":
            scenario_name = sys.argv[2] if len(sys.argv) > 2 else "Entry Trigger - Price >= $220"
            await tester.run_single_scenario(scenario_name)
        else:
            logger.error("Unknown mode. Use 'debug' or 'single <scenario_name>'")
    else:
        # Run all tests
        await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())