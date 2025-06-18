from backend.engine.ib_client import IBClient


if __name__ == "__main__":
    client = IBClient()

    if client.ib.isConnected():
        print("ℹ️ Already connected to IB Gateway — skipping connect()")
    else:
        client.connect(client_id=9)

    # Contract details test
    contract = client.get_contract_details("AAPL")
    if contract:
        print(f"✅ Contract: {contract.symbol}, Exchange: {contract.exchange}, Currency: {contract.currency}")
    else:
        print("❌ Failed to fetch contract for AAPL")

    # Last price test
    last_price = client.get_last_price("AAPL")
    if last_price is not None:
        print(f"💰 Last price for AAPL: ${last_price:.2f}")
    else:
        print("❌ Cannot fetch last price for AAPL")

    # Historical data test
    bars = client.get_historical_data("AAPL", lookback_days=5)
    if bars:
        for bar in bars:
            print(f"🕒 {bar.date} | Open: {bar.open} | High: {bar.high} | Low: {bar.low} | Close: {bar.close} | Volume: {bar.volume}")
    else:
        print("❌ Cannot fetch historical bars for AAPL")

    client.disconnect()
