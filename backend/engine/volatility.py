import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VolatilityCache:
    def __init__(self):
        self.cache = {}

    def get_adr(self, bars, options=None):
        key = (tuple(bars), str(options))
        if key in self.cache:
            return self.cache[key]
        result = calculate_adr(bars, options)
        if result is not None:
            self.cache[key] = result
        return result

    def get_atr(self, bars, options=None):
        key = (tuple(bars), str(options))
        if key in self.cache:
            return self.cache[key]
        result = calculate_atr(bars, options)
        if result is not None:
            self.cache[key] = result
        return result

volatility_cache = VolatilityCache()

def calculate_adr(bars, options=None):
    lookback = options.get("lookback", 20) if options else 20
    if not bars or len(bars) < lookback:
        logger.warning(f"Not enough bars for ADR: {len(bars)} available, {lookback} required")
        return None
    try:
        highs = np.array([bar.high for bar in bars][-lookback:])
        lows = np.array([bar.low for bar in bars][-lookback:])
        closes = np.array([bar.close for bar in bars][-lookback:])
        if not np.all(closes > 0):
            logger.warning("Invalid close prices for ADR calculation")
            return None
        adr_pct = np.mean((highs - lows) / closes) * 100
        return round(adr_pct, 2)
    except Exception as e:
        logger.error(f"Error calculating ADR: {e}")
        return None

def calculate_atr(bars, options=None):
    lookback = options.get("lookback", 14) if options else 14
    if not bars or len(bars) < lookback + 1:
        logger.warning(f"Not enough bars for ATR: {len(bars)} available, {lookback + 1} required")
        return None
    try:
        closes = np.array([bar.close for bar in bars])
        highs = np.array([bar.high for bar in bars])
        lows = np.array([bar.low for bar in bars])
        if not np.all(closes > 0):
            logger.warning("Invalid close prices for ATR calculation")
            return None
        prev_closes = closes[:-1]
        highs = highs[1:]
        lows = lows[1:]
        closes = closes[1:]
        true_ranges = np.maximum(highs - lows, np.abs(highs - prev_closes), np.abs(lows - prev_closes))
        atr_pct = np.mean(true_ranges[-lookback:] / closes[-lookback:]) * 100
        return round(atr_pct, 2)
    except Exception as e:
        logger.error(f"Error calculating ATR: {e}")
        return None