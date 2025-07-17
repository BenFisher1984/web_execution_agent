from backend.engine.market_data.base import MarketDataClient, Tick
from backend.config.settings import get as settings_get
import asyncio
import logging
import websockets
import aiohttp
import json

logger = logging.getLogger(__name__)

class PolygonMarketDataClient(MarketDataClient):
    name = "polygon"
    
    def __init__(self):
        self.api_key = settings_get("polygon_api_key", "")
        self._ws = None
        self._connected = False
        self._subscribed_symbols: set[str] = set()
        self._callbacks: dict[str, list] = {}
        self._task: asyncio.Task | None = None

    async def connect(self) -> None:
        url = f"wss://socket.polygon.io/stocks"
        self._ws = await websockets.connect(url)
        await self._ws.send(json.dumps({"action": "auth", "params": self.api_key}))
        self._connected = True
        self._task = asyncio.create_task(self._listen())
        logger.info("PolygonMarketDataClient connected")

    async def disconnect(self) -> None:
        if self._task:
            self._task.cancel()
        if self._ws:
            await self._ws.close()
        self._connected = False
        logger.info("PolygonMarketDataClient disconnected")

    async def subscribe(self, symbol: str, callback) -> None:
        if not self._connected:
            raise RuntimeError("Not connected")
        self._subscribed_symbols.add(symbol)
        if symbol not in self._callbacks:
            self._callbacks[symbol] = []
        self._callbacks[symbol].append(callback)
        await self._ws.send(json.dumps({"action": "subscribe", "params": f"T.{symbol}"}))
        logger.info(f"Subscribed to {symbol}")

    async def unsubscribe(self, symbol: str) -> None:
        if symbol in self._subscribed_symbols:
            self._subscribed_symbols.remove(symbol)
            await self._ws.send(json.dumps({"action": "unsubscribe", "params": f"T.{symbol}"}))
            logger.info(f"Unsubscribed from {symbol}")


    async def stream_ticks(self):
        if not self._connected:
            raise RuntimeError("Not connected")
        while True:
            await asyncio.sleep(0.1)
            # fake tick scaffold for testing:
            yield {
                "symbol": "AAPL",
                "price": 150.0,
                "ts": int(asyncio.get_event_loop().time() * 1000),
            }

    async def snapshot(self, symbol: str) -> Tick:
        url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}?apiKey={self.api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.error(f"Polygon snapshot API error: {resp.status} - {await resp.text()}")
                    return {
                        "symbol": symbol,
                        "price": 0.0,
                        "ts": 0,
                    }
                
                data = await resp.json()
                last_trade = data.get("ticker", {}).get("lastTrade", {})
                price = last_trade.get("p", 0.0)
                logger.info(f"Retrieved snapshot for {symbol}: ${price}")
                return {
                    "symbol": symbol,
                    "price": price,
                    "ts": last_trade.get("t", 0),
                }

    async def get_historical_data(self, symbol: str, lookback_days: int):
        """Fetch historical daily bars from Polygon"""
        from datetime import datetime, timedelta
        
        # Calculate the date range properly
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Format dates as YYYY-MM-DD
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_str}/{end_str}?apiKey={self.api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.error(f"Polygon API error: {resp.status} - {await resp.text()}")
                    return []
                
                data = await resp.json()
                results = data.get("results", [])
                
                logger.info(f"Retrieved {len(results)} bars for {symbol} from Polygon")
                
                # Convert Polygon bars to a format compatible with the volatility calculations
                bars = []
                for bar_data in results:
                    bar = type('Bar', (), {
                        'open': bar_data.get('o'),
                        'high': bar_data.get('h'),
                        'low': bar_data.get('l'),
                        'close': bar_data.get('c'),
                        'volume': bar_data.get('v'),
                        'timestamp': bar_data.get('t')
                    })()
                    bars.append(bar)
                
                return bars

    async def get_contract_details(self, symbol: str):
        """Get contract details for a symbol"""
        # For Polygon, we'll return a simple contract object
        # In a real implementation, you might want to fetch more details
        return type('Contract', (), {
            'symbol': symbol.upper(),
            'exchange': 'NASDAQ',  # Default assumption
            'currency': 'USD'
        })()

    async def get_last_price(self, symbol: str) -> float:
        """Get the last price for a symbol"""
        try:
            tick = await self.snapshot(symbol)
            return tick.get("price", 0.0)
        except Exception as e:
            logger.error(f"Failed to get last price for {symbol}: {e}")
            return 0.0

    async def _listen(self):
        try:
            async for message in self._ws:
                data = json.loads(message)
                if isinstance(data, list):
                    for tick in data:
                        if tick.get("ev") == "T":
                            symbol = tick.get("sym")
                            price = tick.get("p")
                            ts = tick.get("t")
                            if symbol and price and symbol in self._callbacks:
                                tick_data = {
                                    "symbol": symbol,
                                    "price": price,
                                    "ts": ts,
                                }
                                for cb in self._callbacks[symbol]:
                                    await cb(tick_data)
        except Exception as e:
            logger.error(f"Polygon listener failed: {e}")
