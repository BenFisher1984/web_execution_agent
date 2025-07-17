#!/usr/bin/env python3
"""
Simple tick injection script for testing trade execution
"""

import asyncio
import json
import requests
from datetime import datetime

async def inject_tick(symbol="AAPL", price=195.0):
    """Inject a tick at the specified price via API"""
    
    # Create tick data
    tick_data = {
        "symbol": symbol,
        "price": price,
        "timestamp": datetime.now().isoformat(),
        "volume": 100,
        "bid": price - 0.01,
        "ask": price + 0.01
    }
    
    print(f"🎯 Injecting tick for {symbol} at ${price}")
    print(f"📊 Tick data: {json.dumps(tick_data, indent=2)}")
    
    try:
        # Send tick via API endpoint
        response = requests.post(
            "http://localhost:8000/inject_tick",
            json=tick_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Tick injection successful!")
            print(f"📡 Response: {response.text}")
        else:
            print(f"❌ Tick injection failed: {response.status_code}")
            print(f"📡 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error injecting tick: {e}")

if __name__ == "__main__":
    asyncio.run(inject_tick()) 