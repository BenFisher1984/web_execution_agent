#!/usr/bin/env python3
"""
Quick trade status checker
"""

import json
import requests

def check_trade_status():
    """Check current AAPL trade status"""
    try:
        response = requests.get("http://localhost:8000/trades")
        if response.status_code == 200:
            trades = response.json()
            for trade in trades:
                if trade.get("symbol") == "AAPL":
                    print("🍎 AAPL Trade Status:")
                    print(f"  Trade Status: {trade.get('trade_status')}")
                    print(f"  Order Status: {trade.get('order_status')}")
                    print(f"  Filled Qty: {trade.get('filled_qty', 'N/A')}")
                    print(f"  Fill Price: ${trade.get('executed_price', 'N/A')}")
                    print(f"  Current Trailing Stop: {trade.get('current_trailing_stop', 'N/A')}")
                    print(f"  Active Stop: {trade.get('active_stop', 'N/A')}")
                    
                    # Check rule configuration
                    print(f"\n📋 Rule Configuration:")
                    print(f"  Entry Rules: {trade.get('entry_rules', [])}")
                    print(f"  Stop Rules: {trade.get('initial_stop_rules', [])}")
                    print(f"  Trailing Rules: {trade.get('trailing_stop_rules', [])}")
                    print(f"  Take Profit Rules: {trade.get('take_profit_rules', [])}")
                    
                    return trade
            print("❌ No AAPL trade found")
        else:
            print(f"❌ Failed to get trades: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    check_trade_status()