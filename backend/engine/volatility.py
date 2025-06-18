"""
volatility.py

Provides volatility metrics for trade evaluation, including:
- ADR (Average Daily Range)
- ATR (Average True Range)

Currently supports user-defined lookback only.
Future options (e.g., output format, basis, style) are structurally supported.
"""

import numpy as np

def calculate_adr(bars, options=None):
    """
    Calculates Average Daily Range (ADR) as a percentage of close price.
    
    Args:
        bars (list): List of historical bars (BarData)
        options (dict): Supports 'lookback' (default=20)
    
    Returns:
        float: ADR% rounded to 2 decimals, or None if not enough data
    """
    lookback = options.get("lookback", 20) if options else 20

    if len(bars) < lookback:
        print(f"⚠️ Not enough bars for ADR: {len(bars)} available, {lookback} required")
        return None

    highs = np.array([bar.high for bar in bars][-lookback:])
    lows = np.array([bar.low for bar in bars][-lookback:])
    closes = np.array([bar.close for bar in bars][-lookback:])

    adr_pct = np.mean((highs - lows) / closes) * 100
    return round(adr_pct, 2)

def calculate_atr(bars, options=None):
    """
    Calculates Average True Range (ATR) as a percentage of close price.

    Args:
        bars (list): List of historical bars (BarData)
        options (dict): Supports 'lookback' (default=14)

    Returns:
        float: ATR% rounded to 2 decimals, or None if not enough data
    """
    lookback = options.get("lookback", 14) if options else 14

    if len(bars) < lookback + 1:
        print(f"⚠️ Not enough bars for ATR: {len(bars)} available, {lookback + 1} required")
        return None

    closes = np.array([bar.close for bar in bars])
    highs = np.array([bar.high for bar in bars])
    lows = np.array([bar.low for bar in bars])

    prev_closes = closes[:-1]
    highs = highs[1:]
    lows = lows[1:]
    closes = closes[1:]

    true_ranges = np.maximum(highs - lows, np.abs(highs - prev_closes), np.abs(lows - prev_closes))
    atr_pct = np.mean(true_ranges[-lookback:] / closes[-lookback:]) * 100

    return round(atr_pct, 2)
