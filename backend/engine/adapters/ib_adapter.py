# backend/engine/adapters/ib_adapter.py

from .base import BrokerAdapter, Order
from ib_insync import IB, Stock
import asyncio
import math
import logging
import time
from typing import Optional, Dict, Any

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
        self._connection_attempts = 0
        self._max_connection_attempts = 5
        self._connection_backoff = 2.0
        self._last_connection_attempt = 0
        self._connection_lock = asyncio.Lock()
        self._connection_in_progress = False  # Prevent multiple simultaneous connections
        self._connection_task = None  # Track ongoing connection attempt
        super().__init__(name="ib")

    async def connect(self, client_id=None, max_retries=3):
        """Enhanced connection with retry logic and error handling"""
        # If connection is already in progress, wait for it
        if self._connection_in_progress and self._connection_task:
            try:
                await self._connection_task
                return
            except Exception:
                # If the other connection failed, we can try again
                pass
        
        async with self._connection_lock:
            # Double-check if we're already connected
            if self.is_connected():
                logger.debug("Already connected to IB Gateway")
                return
            
            # Prevent multiple simultaneous connection attempts
            if self._connection_in_progress:
                logger.warning("Connection already in progress, waiting...")
                return
            
            self._connection_in_progress = True
            self._connection_task = asyncio.create_task(self._connect_internal(client_id, max_retries))
            
            try:
                await self._connection_task
            finally:
                self._connection_in_progress = False
                self._connection_task = None

    async def _connect_internal(self, client_id=None, max_retries=3):
        """Internal connection method with proper error handling"""
        # Prevent rapid reconnection attempts
        current_time = time.time()
        if current_time - self._last_connection_attempt < 2.0:  # Increased from 1.0 to 2.0
            await asyncio.sleep(2.0)
        
        self._last_connection_attempt = current_time
        
        for attempt in range(max_retries):
            try:
                cid = client_id if client_id is not None else self.client_id
                
                # Try different client IDs if the default is in use
                if attempt > 0:
                    cid = self.client_id + attempt
                    logger.info(f"Retrying connection with client ID {cid}")
                
                # Disconnect any existing connection first
                if self.ib.isConnected():
                    logger.info("Disconnecting existing connection before reconnecting...")
                    self.ib.disconnect()
                    await asyncio.sleep(1.0)  # Give time for disconnect
                
                await asyncio.wait_for(
                    self.ib.connectAsync(self.host, self.port, clientId=cid),
                    timeout=15.0  # Increased timeout
                )
                
                # Verify connection is actually working
                if self.ib.isConnected():
                    logger.info(f"Successfully connected to IB Gateway with client ID {cid}")
                    self.client_id = cid  # Update to the working client ID
                    self._connection_attempts = 0
                    return
                else:
                    raise Exception("Connection established but not verified")
                    
            except asyncio.TimeoutError:
                logger.error(f"Connection timeout (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                error_msg = str(e)
                if "client id is already in use" in error_msg.lower():
                    logger.warning(f"Client ID {cid} in use, will retry with different ID")
                else:
                    logger.error(f"Connection failed (attempt {attempt + 1}/{max_retries}): {e}")
            
            # Exponential backoff between attempts
            if attempt < max_retries - 1:
                wait_time = self._connection_backoff * (2 ** attempt)
                logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        # If we get here, all retries failed
        error_msg = f"Failed to connect to IB Gateway after {max_retries} attempts"
        logger.error(error_msg)
        raise Exception(error_msg)

    async def disconnect(self):
        """Enhanced disconnect with error handling"""
        try:
            if self.ib.isConnected():
                self.ib.disconnect()
                logger.info("Successfully disconnected from IB Gateway")
            else:
                logger.info("Already disconnected from IB Gateway")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            # Don't raise - disconnect errors shouldn't crash the app

    def is_connected(self) -> bool:
        """Check connection status with error handling"""
        try:
            return self.ib.isConnected()
        except Exception as e:
            logger.error(f"Error checking connection status: {e}")
            return False

    async def _ensure_connected(self) -> bool:
        """Ensure we have a valid connection, reconnect if needed"""
        if self.is_connected():
            return True
        
        logger.warning("IB connection lost, attempting to reconnect...")
        try:
            await self.connect()
            return True
        except Exception as e:
            logger.error(f"Failed to reconnect to IB: {e}")
            return False

    async def get_contract_details(self, symbol: str):
        """Get contract details with connection retry logic"""
        if not await self._ensure_connected():
            logger.error(f"Cannot get contract details for {symbol}: not connected")
            return None
            
        try:
            # Check cache first
            if symbol in self.contract_cache:
                return self.contract_cache[symbol]
            
            contract = Stock(symbol, 'SMART', 'USD')
            await asyncio.wait_for(
                self.ib.qualifyContractsAsync(contract),
                timeout=5.0
            )
            
            # Cache the result
            self.contract_cache[symbol] = contract
            logger.debug(f"Cached contract details for {symbol}")
            return contract
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting contract details for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Failed to get contract details for {symbol}: {e}")
            return None

    async def get_contract_details_batch(self, symbols: list[str]):
        """Get contract details for multiple symbols with error handling"""
        if not await self._ensure_connected():
            logger.error(f"Cannot get contract details batch: not connected")
            return {}
            
        try:
            results = {}
            tasks = []
            
            # Create tasks for each symbol
            for symbol in symbols:
                if symbol not in self.contract_cache:
                    task = self.get_contract_details(symbol)
                    tasks.append((symbol, task))
                else:
                    # Use cached result
                    results[symbol] = self.contract_cache[symbol]
            
            # Execute tasks concurrently
            if tasks:
                symbol_list, task_list = zip(*tasks)
                completed = await asyncio.gather(*task_list, return_exceptions=True)
                
                for symbol, result in zip(symbol_list, completed):
                    if isinstance(result, Exception):
                        logger.error(f"Failed to get contract details for {symbol}: {result}")
                        results[symbol] = None
                    else:
                        results[symbol] = result
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get contract details batch: {e}")
            return {}

    async def get_last_price(self, symbol):
        """Enhanced get_last_price with fallback and error handling"""
        if not await self._ensure_connected():
            logger.error(f"Cannot fetch last price for {symbol}: not connected")
            return None
            
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
                    if hasattr(last_bar, 'close') and last_bar.close is not None:
                        logger.info(f"Using fallback close price for {symbol}: ${last_bar.close}")
                        return last_bar.close
                    else:
                        logger.error(f"No valid close price in historical data for {symbol}")
                        return None
                else:
                    logger.error(f"No historical data available for fallback for {symbol}")
                    return None

        except Exception as e:
            logger.error(f"get_last_price failed for {symbol}: {e}")
            return None

    async def get_historical_data(self, symbol, lookback_days=30):
        """Enhanced historical data with error handling"""
        if not await self._ensure_connected():
            logger.error(f"Cannot fetch historical data for {symbol}: not connected")
            return None
            
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

    async def place_order(self, order: Order) -> str:
        """Enhanced order placement with error handling"""
        if not await self._ensure_connected():
            raise Exception("Cannot place order: not connected to IB")
            
        try:
            contract = await self.get_contract_details(order['symbol'])
            if not contract:
                raise Exception(f"Contract not found for {order['symbol']}")
            
            # Create IB order
            from ib_insync import Order as IBOrder
            ib_order = IBOrder()
            ib_order.action = order['side'].upper()
            ib_order.totalQuantity = order['qty']
            ib_order.orderType = order['order_type'].upper()
            ib_order.tif = order['tif'].upper()
            
            if order.get('price') is not None:
                try:
                    ib_order.lmtPrice = float(order['price'])
                except (ValueError, TypeError):
                    logger.error(f"Invalid price value for order: {order['price']}")
                    raise Exception(f"Invalid price value: {order['price']}")
            
            # Submit order
            trade = self.ib.placeOrder(contract, ib_order)
            
            # Wait for order to be submitted with timeout
            timeout = 10.0
            start_time = time.time()
            while not trade.orderStatus.status and (time.time() - start_time) < timeout:
                await asyncio.sleep(0.1)
            
            if not trade.orderStatus.status:
                raise Exception("Order submission timeout")
            
            logger.info(f"Order placed successfully: {trade.order.orderId}")
            return str(trade.order.orderId)
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise

    async def execute_order(self, order_details):
        """Execute order with error handling"""
        try:
            return await self.place_order(order_details)
        except Exception as e:
            logger.error(f"Failed to execute order: {e}")
            raise

    async def get_order_status(self, order_id):
        """Get order status with error handling"""
        if not await self._ensure_connected():
            return {"order_id": order_id, "status": "unknown", "error": "not connected"}
            
        try:
            # This is a simplified implementation
            # In production, you'd query the actual order status from IB
            return {"order_id": order_id, "status": "filled"}
        except Exception as e:
            logger.error(f"Failed to get order status for {order_id}: {e}")
            return {"order_id": order_id, "status": "unknown", "error": str(e)}

    async def subscribe_market_data(self, symbol):
        """Subscribe to market data with error handling"""
        if not await self._ensure_connected():
            logger.error(f"Cannot subscribe to market data for {symbol}: not connected")
            return False
            
        try:
            contract = await self.get_contract_details(symbol)
            if not contract:
                logger.error(f"Cannot subscribe: contract not found for {symbol}")
                return False
                
            # Subscribe to market data
            self.ib.reqMktData(contract)
            logger.info(f"Subscribed to market data for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to market data for {symbol}: {e}")
            return False

    async def unsubscribe_market_data(self, symbol):
        """Unsubscribe from market data with error handling"""
        try:
            contract = await self.get_contract_details(symbol)
            if contract:
                self.ib.cancelMktData(contract)
                logger.info(f"Unsubscribed from market data for {symbol}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe from market data for {symbol}: {e}")

    async def get_positions(self):
        """Get positions with error handling"""
        if not await self._ensure_connected():
            logger.error("Cannot get positions: not connected to IB")
            return []
            
        try:
            positions = await asyncio.wait_for(
                self.ib.reqPositionsAsync(),
                timeout=10.0
            )
            return positions
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    async def get_history(self, symbol: str, days: int):
        """Get historical data for volatility calculations"""
        try:
            bars = await self.get_historical_data(symbol, lookback_days=days)
            if bars:
                # Extract close prices for volatility calculation
                return [bar.close for bar in bars if hasattr(bar, 'close') and bar.close is not None]
            return []
        except Exception as e:
            logger.error(f"Failed to get history for {symbol}: {e}")
            return []

    async def get_market_price(self, symbol: str):
        """Get current market price"""
        return await self.get_last_price(symbol)

    async def stream_fills(self):
        """Stream fills with error handling"""
        try:
            while self.is_connected():
                try:
                    # This is a simplified implementation
                    # In production, you'd implement proper fill streaming
                    await asyncio.sleep(1.0)
                    yield None  # No fills for now
                except asyncio.CancelledError:
                    logger.debug("Fill stream cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in fill stream: {e}")
                    await asyncio.sleep(5.0)  # Wait before retry
        except Exception as e:
            logger.error(f"Fill stream failed: {e}")
