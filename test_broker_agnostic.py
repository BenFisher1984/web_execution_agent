#!/usr/bin/env python3
"""
Test script to verify broker-agnostic architecture is working.
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.engine.market_data.factory import get_market_data_client
from backend.engine.adapters.factory import get_adapter
from backend.config.settings import get as settings_get

async def test_broker_agnostic():
    print("🧪 Testing Broker-Agnostic Architecture")
    print("=" * 50)
    
    # Test 1: Market Data Client (should be Polygon)
    print("\n1. Testing Market Data Client...")
    try:
        md_client = get_market_data_client("polygon")
        print(f"✅ Market data client created: {md_client.name}")
        
        # Test historical data
        bars = await md_client.get_historical_data("AAPL", lookback_days=5)
        print(f"✅ Historical data retrieved: {len(bars)} bars")
        
        # Test last price
        last_price = await md_client.get_last_price("AAPL")
        print(f"✅ Last price retrieved: ${last_price}")
        
    except Exception as e:
        print(f"❌ Market data client test failed: {e}")
    
    # Test 2: Execution Adapter (should be IB)
    print("\n2. Testing Execution Adapter...")
    try:
        exec_adapter = get_adapter("ib")
        print(f"✅ Execution adapter created: {exec_adapter.name}")
        
        # Test connection (this will fail if IB Gateway is not running)
        print("⚠️  Note: IB connection test skipped (requires IB Gateway)")
        
    except Exception as e:
        print(f"❌ Execution adapter test failed: {e}")
    
    # Test 3: Settings
    print("\n3. Testing Configuration...")
    try:
        market_provider = settings_get("market_data_provider", "stub")
        exec_provider = settings_get("execution_adapter", "stub")
        print(f"✅ Market data provider: {market_provider}")
        print(f"✅ Execution adapter: {exec_provider}")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Broker-agnostic architecture test completed!")

if __name__ == "__main__":
    asyncio.run(test_broker_agnostic()) 