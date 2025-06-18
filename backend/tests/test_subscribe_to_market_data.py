# backend/test_subscribe_to_market_data.py

from engine.ib_client import IBClient
from ib_insync import Ticker

def on_tick(ticker: Ticker):
    symbol = ticker.contract.symbol
    price = ticker.last or ticker.close
    if price is not None:
        print(f"📈 Tick received for {symbol}: ${price:.2f}")
    else:
        print(f"⚠️ Tick received for {symbol} but price unavailable")

def main():
    client = IBClient()
    client.connect()

    # Subscribe to a symbol (market should be open to see ticks)
    client.subscribe_to_market_data("AAPL", on_tick)

    print("⏳ Waiting for ticks (press Ctrl+C to exit)...")
    try:
        client.ib.run()  # Keeps the event loop running
    except KeyboardInterrupt:
        print("🛑 Interrupted by user.")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
