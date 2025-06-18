from backend.engine.ib_client import IBClient
from backend.engine.volatility import calculate_adr, calculate_atr


if __name__ == "__main__":
    client = IBClient()
    client.connect()

    bars = client.get_historical_data("AAPL", lookback_days=30)

    if bars:
        adr = calculate_adr(bars, options={"lookback": 20})
        atr = calculate_atr(bars, options={"lookback": 14})

        if adr is not None:
            print(f"📊 ADR (20d): {adr}%")
        if atr is not None:
            print(f"📊 ATR (14d): {atr}%")

    client.disconnect()
