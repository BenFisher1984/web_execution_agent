from ib_insync import IB, Stock
import math

class IBClient:
    def __init__(self, host='127.0.0.1', port=4002, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.subscribed_contracts = {}

    def connect(self, client_id=None):
        try:
            cid = client_id if client_id is not None else self.client_id
            self.ib.connect(self.host, self.port, clientId=cid)
            print("✅ Connected to IB Gateway")
        except Exception as e:
            print(f"❌ Connection failed: {e}")

    def disconnect(self):
        self.ib.disconnect()
        print("🔌 Disconnected from IB Gateway")

    def get_contract_details(self, symbol):
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            details = self.ib.reqContractDetails(contract)
            if details:
                return details[0].contract
            else:
                print(f"⚠️ No contract details found for {symbol}")
                return None
        except Exception as e:
            print(f"❌ Failed to fetch contract for {symbol}: {e}")
            return None

    def get_last_price(self, symbol):
        try:
            contract = self.get_contract_details(symbol)
            if not contract:
                print(f"❌ Cannot fetch last price: contract not found for {symbol}")
                return None

            ticker = self.ib.reqMktData(contract, "", False, False)
            self.ib.sleep(1)

            last_price = ticker.last
            close_price = ticker.close

            if last_price is not None and not math.isnan(last_price):
                print(f"✅ Using last trade price for {symbol}")
                return last_price
            elif close_price is not None and not math.isnan(close_price):
                print(f"⚠️ Using close price for {symbol} (last price unavailable)")
                return close_price
            else:
                print(f"⚠️ No usable last or close price for {symbol}")
                return None
        except Exception as e:
            print(f"❌ Failed to fetch last price for {symbol}: {e}")
            return None

    def get_historical_data(self, symbol, lookback_days=30):
        try:
            contract = self.get_contract_details(symbol)
            if not contract:
                print(f"❌ Cannot fetch history: contract not found for {symbol}")
                return None

            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=f'{lookback_days} D',
                barSizeSetting='1 day',
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )

            if not bars:
                print(f"⚠️ No historical data returned for {symbol}")
                return None

            print(f"📈 Retrieved {len(bars)} bars for {symbol}")
            return bars

        except Exception as e:
            print(f"❌ Failed to fetch historical data for {symbol}: {e}")
            return None

    def subscribe_to_market_data(self, symbol, callback):
        """
        Subscribes to real-time tick data for the given symbol.
        Calls the provided callback on price updates.
        """
        try:
            if symbol in self.subscribed_contracts:
                print(f"ℹ️ Already subscribed to {symbol}")
                return

            contract = self.get_contract_details(symbol)
            if not contract:
                return

            ticker = self.ib.reqMktData(contract, "", False, False)

            def on_update(t):
                callback(t)

            ticker.updateEvent += on_update
            self.subscribed_contracts[symbol] = ticker
            print(f"📡 Subscribed to market data for {symbol}")

        except Exception as e:
            print(f"❌ Failed to subscribe to market data for {symbol}: {e}")

ib_client = IBClient()
ib_client.connect()
ib = ib_client.ib  # <- export the underlying ib_insync instance
