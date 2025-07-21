#!/usr/bin/env python3
"""
Quick test runner for AAPL workflow testing
"""

import sys
import os
import asyncio

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from tests.test_aapl_workflow import AAPLWorkflowTester

async def main():
    """Run AAPL workflow tests"""
    print("🍎 AAPL Trade Workflow Testing Framework")
    print("=" * 50)
    
    # Create tester instance
    tester = AAPLWorkflowTester()
    
    # Run comprehensive tests
    results = await tester.run_comprehensive_tests()
    
    # Optional: Run debug mode for detailed inspection
    if "--debug" in sys.argv:
        print("\n🔍 Starting Debug Mode...")
        await tester.run_debug_mode()

if __name__ == "__main__":
    asyncio.run(main())