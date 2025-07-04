# backend/engine/adapters/ib_adapter.py

from .base import BrokerAdapter
from ib_insync import IB, Stock
import asyncio
import math
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class IBAdapter(BrokerAdapter):

    def __init__(self, host='127.0.0.1', port=7497, client_id=2):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.subscribed_contracts = {}
        self.contract_cache = {}
        self.volatility_cache = {}

    async def connect(self, client_id=None, max_retries=3):
        for attempt in range(max_retries):
            try:
                cid = client_id if client_id is not None else self.client_id
                await asyncio.wait_for(
                    self.ib.connectAsync(self.host, self.port, clientId=cid),
                    timeout=10.0
                )
                logger.info("Connected to IB Gateway")
                return
            except asyncio.TimeoutError:
                logger.error(f"Connection timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Connection failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
        logger.error("Max retries reached for IB Gateway connection")
        raise Exception("Failed to connect to IB Gateway")

    async def disconnect(self):
        try:
            self.ib.disconnect()
            logger.info("Disconnected from IB Gateway")
        except Exception as e:
            logger.error(f"Disconnect failed: {e}")

    def is_connected(self) -> bool:
        return self.ib.isConnected()

    async def get_contract_details(self, symbol):
        try:
            if symbol in self.contract_cache:
                logger.debug(f"Using cached contract for {symbol}")
                return self.contract_cache[symbol]

            contract = Stock(symbol, 'SMART', 'USD')
            details = await asyncio.wait_for(
                self.ib.reqContractDetailsAsync(contract),
                timeout=5.0
            )
            if details:
                self.contract_cache[symbol] = details[0].contract
                return details[0].contract
            else:
                logger.warning(f"No contract details found for {symbol}")
                return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching contract for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch contract for {symbol}: {e}")
            return None

    async def get_contract_details_batch(self, symbols):
        try:
            tasks = [self.get_contract_details(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return {
                symbol: result
                for symbol, result in zip(symbols, results)
                if not isinstance(result, Exception)
            }
        except Exception as e:
            logger.error(f"Failed to fetch batch contracts: {e}")
            return {}

    async def get_last_price(self, symbol):
        try:
            contract = await self.get_contract_details(symbol)
            if not contract:
                logger.error(f"Cannot fetch last price: contract not found for {symbol}")
                return None

            try:
                tickers = await asyncio.wait_for(
                    self.ib.reqTickersAsync(contract),
                    timeout=5.0
                )
                if not tickers:
                    logger.warning(f"No ticker data for {symbol}")
                    raise Exception("No ticker data")

                ticker = tickers[0]
                last_price = ticker.last
                close_price = ticker.close

                if last_price is not None and not math.isnan(last_price):
                    logger.debug(f"Using last trade price for {symbol}: ${last_price}")
                    return last_price
                elif close_price is not None and not math.isnan(close_price):
                    logger.debug(f"Using close price for {symbol}: ${close_price}")
                    return close_price
                else:
                    raise Exception("No usable last or close price")

            except (asyncio.TimeoutError, Exception) as e:
                logger.warning(f"Live market data unavailable for {symbol}, falling back to historical: {e}")
                bars = await self.get_historical_data(symbol, lookback_days=2)
                if bars:
                    last_bar = bars[-1]
                    logger.info(f"Using fallback close price for {symbol}: ${last_bar.close}")
                    return last_bar.close
                else:
                    logger.error(f"No historical data available for fallback for {symbol}")
                    return None

        except Exception as e:
            logger.error(f"get_last_price failed for {symbol}: {e}")
            return None

    async def get_historical_data(self, symbol, lookback_days=30):
        try:
            contract = await self.get_contract_details(symbol)
            if not contract:
                logger.error(f"Cannot fetch history: contract not found for {symbol}")
                return None

            bars = await asyncio.wait_for(
                self.ib.reqHistoricalDataAsync(
                    contract,
                    endDateTime='',
                    durationStr=f'{lookback_days} D',
                    barSizeSetting='1 day',
                    whatToShow='TRADES',
                    useRTH=True,
                    formatDate=1
                ),
                timeout=10.0
            )

            if not bars:
                logger.warning(f"No historical data returned for {symbol}")
                return None

            logger.info(f"Retrieved {len(bars)} bars for {symbol}")
            return bars
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching historical data for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            return None

    async def subscribe_market_data(self, symbol):
        try:
            if symbol in self.subscribed_contracts:
                logger.info(f"Already subscribed to {symbol}")
                return

            contract = await self.get_contract_details(symbol)
            if not contract:
                logger.error(f"Cannot subscribe: contract not found for {symbol}")
                return

            ticker = self.ib.reqMktData(contract, "", False, False)

            def on_update(t):
                logging.debug(f"Market data update: {t}")
                # you could connect this to an event dispatcher later
            ticker.updateEvent += on_update

            self.subscribed_contracts[symbol] = ticker
            logger.info(f"Subscribed to market data for {symbol}")
        except Exception as e:
            logger.error(f"Failed to subscribe to market data for {symbol}: {e}")

    async def subscribe_batch_market_data(self, symbols, callback):
        try:
            contracts = []
            for symbol in symbols:
                contract = await self.get_contract_details(symbol)
                if contract:
                    contracts.append(contract)
                else:
                    logger.warning(f"Skipping {symbol} — no contract found")

            if not contracts:
                logger.warning("No valid contracts to subscribe in batch")
                return

            tickers = await asyncio.wait_for(
                self.ib.reqTickersAsync(*contracts),
                timeout=10.0
            )
            for ticker in tickers:
                ticker.updateEvent += callback
                symbol = ticker.contract.symbol
                self.subscribed_contracts[symbol] = ticker
                logger.info(f"Subscribed to batched market data for {symbol}")
        except asyncio.TimeoutError:
            logger.error("Timeout subscribing to batch market data")
        except Exception as e:
            logger.error(f"Failed to subscribe to batch market data: {e}")

    async def execute_order(self, order_details):
        # for now, treat same as place_order
        return await self.place_order(order_details)

    async def get_order_status(self, order_id):
        # IB logic placeholder — for now, pretend filled
        return {"order_id": order_id, "status": "filled"}

    async def unsubscribe_market_data(self, symbol):
        # optionally cancel IB market data subscription
        pass
