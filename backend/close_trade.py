#!/usr/bin/env python3
"""
Simple script to close a trade using mark_trade_closed()
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.engine.trade_manager import TradeManager
from backend.engine.adapters.factory import get_adapter
from backend.engine.market_data.factory import get_market_data_client
from backend.engine.order_executor import OrderExecutor

async def close_trade(symbol="AAPL", exit_price=209.0, exit_qty=188):
    """Close a trade using mark_trade_closed"""
    
    print(f"🔄 Closing trade: {symbol} - {exit_qty} shares @ ${exit_price}")
    
    try:
        # Initialize the same components as the main app
        exec_adapter = get_adapter('ib')
        md_client = get_market_data_client('ib')
        
        # Create OrderExecutor first
        order_executor = OrderExecutor(exec_adapter)
        
        # Create TradeManager with OrderExecutor
        trade_manager = TradeManager(
            exec_adapter, 
            md_client=md_client, 
            order_executor=order_executor
        )
        
        # Set the trade_manager reference in OrderExecutor
        order_executor.trade_manager = trade_manager
        
        # Close the trade
        await trade_manager.mark_trade_closed(symbol, exit_price, exit_qty)
        
        print(f"✅ Trade closed successfully: {symbol}")
        print(f"   Exit: {exit_qty} shares @ ${exit_price}")
        print(f"   Check the JSON file for updated status")
        
    except Exception as e:
        print(f"❌ Error closing trade: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main entry point"""
    if len(sys.argv) == 1:
        # Default: close AAPL at $209 for 188 shares
        print("🎯 Default: Closing AAPL trade at $209 for 188 shares")
        asyncio.run(close_trade())
    elif len(sys.argv) == 4:
        # Custom: symbol, price, quantity
        symbol = sys.argv[1].upper()
        try:
            price = float(sys.argv[2])
            quantity = int(sys.argv[3])
            print(f"🎯 Closing {symbol} trade at ${price} for {quantity} shares")
            asyncio.run(close_trade(symbol, price, quantity))
        except ValueError:
            print("❌ Invalid price or quantity format")
    else:
        print("Usage:")
        print("  python close_trade.py                    # Close AAPL at $209 for 188 shares")
        print("  python close_trade.py AAPL 209.0 188     # Close specific trade")

if __name__ == "__main__":
    main()