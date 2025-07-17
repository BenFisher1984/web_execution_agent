# Moving Averages Guide

## Overview

Your trading system now supports sophisticated moving average functionality for both technical analysis and automated trading strategies. This guide explains how to use moving averages effectively in your trading system.

## Available Moving Averages

### 1. Simple Moving Average (SMA)
- **Description**: Arithmetic average of prices over a specified period
- **Formula**: `SMA = (P1 + P2 + ... + Pn) / n`
- **Use Case**: Trend identification, support/resistance levels
- **Default Period**: 20 days

### 2. Exponential Moving Average (EMA)
- **Description**: Weighted average that gives more importance to recent prices
- **Formula**: `EMA = (Price × k) + (Previous EMA × (1 - k))` where `k = 2/(n+1)`
- **Use Case**: Trend following, momentum analysis
- **Default Period**: 21 days

## Moving Average Functions

### Basic Calculations
```python
from backend.engine.indicators import calculate_sma, calculate_ema

# Calculate SMA
sma_20 = calculate_sma(prices, 20)

# Calculate EMA
ema_21 = calculate_ema(prices, 21)
```

### EMA Crossover Detection
```python
from backend.engine.indicators import calculate_ema_crossover

# Detect EMA crossover (8-period vs 21-period)
crossover_data = calculate_ema_crossover(prices, 8, 21)

# Results include:
# - crossover: True if crossover detected
# - signal: 'bullish' or 'bearish'
# - fast_ema: Current fast EMA value
# - slow_ema: Current slow EMA value
```

### Moving Average Comparisons
```python
from backend.engine.indicators import get_moving_average_value

# Check if price is above/below moving average
ma_config = {"type": "ema", "length": 21}
ma_value = get_moving_average_value(prices, ma_config)
is_above_ma = current_price > ma_value
```

## Strategy Integration

### 1. Entry Conditions
You can use moving averages as entry conditions:

```json
{
  "type": "moving_average_above",
  "symbol": "AAPL",
  "ma_config": {
    "type": "ema",
    "length": 21
  }
}
```

### 2. EMA Crossover Entries
```json
{
  "type": "ema_crossover",
  "symbol": "AAPL",
  "ema_fast": 8,
  "ema_slow": 21,
  "signal": "bullish"
}
```

### 3. Contingent Order Triggers
Moving averages can trigger contingent orders:

```json
{
  "order_type": "market",
  "quantity": 50,
  "quantity_type": "percentage",
  "trigger_condition": {
    "type": "ema_crossover",
    "ema_fast": 8,
    "ema_slow": 21,
    "signal": "bearish"
  }
}
```

## Example Strategies

### 1. EMA Crossover Strategy
- **Entry**: Buy when 8-period EMA crosses above 21-period EMA
- **Exit**: Sell when 8-period EMA crosses below 21-period EMA
- **Risk Management**: Stop loss at -5% unrealized PnL

### 2. Moving Average Support Strategy
- **Entry**: Buy when price is above 21-period EMA
- **Exit**: Sell when price falls below 50-period SMA
- **Risk Management**: Stop loss at -3% unrealized PnL

### 3. Multi-Timeframe Strategy
- **Entry**: Buy when price > 21 EMA AND 8 EMA > 21 EMA
- **Exit**: Sell when price < 50 SMA OR 8 EMA < 21 EMA
- **Risk Management**: Trailing stop based on ADR

## Technical Implementation

### Rolling Window
The system uses a `RollingWindow` class to maintain price history:

```python
from backend.engine.indicators import RollingWindow

# Create rolling window for 50 periods
window = RollingWindow(50)

# Add new prices
window.append(current_price)

# Get all prices for calculation
prices = window.get_window()
```

### Error Handling
The system includes robust error handling:

- **Insufficient Data**: Returns appropriate error messages
- **Invalid Parameters**: Validates moving average types and periods
- **Calculation Errors**: Graceful degradation with logging

## Best Practices

### 1. Period Selection
- **Short-term**: 5-10 periods for quick signals
- **Medium-term**: 20-50 periods for trend following
- **Long-term**: 100+ periods for major trends

### 2. Multiple Timeframes
- Use different periods for different purposes
- Combine short and long moving averages
- Consider market volatility when selecting periods

### 3. Risk Management
- Always use stop losses with moving average strategies
- Consider volatility (ADR/ATR) for position sizing
- Monitor multiple indicators, not just moving averages

### 4. Backtesting
- Test strategies with historical data
- Validate moving average calculations
- Monitor performance across different market conditions

## Configuration Examples

### Frontend Configuration
The system supports moving averages in the UI:

```json
{
  "primary_source": "EMA 21",
  "condition": ">=",
  "secondary_source": "Price"
}
```

### Strategy Configuration
```json
{
  "id": "ema_strategy",
  "name": "EMA Crossover",
  "entry_condition": {
    "type": "ema_crossover",
    "ema_fast": 8,
    "ema_slow": 21,
    "signal": "bullish"
  },
  "contingent_orders": [
    {
      "order_type": "market",
      "quantity": 100,
      "quantity_type": "percentage",
      "trigger_condition": {
        "type": "ema_crossover",
        "ema_fast": 8,
        "ema_slow": 21,
        "signal": "bearish"
      }
    }
  ]
}
```

## Testing

Run the moving average tests:

```bash
cd backend
python tests/test_indicators.py
```

This will test:
- SMA and EMA calculations
- EMA crossover detection
- Moving average utility functions
- Error handling for insufficient data

## Integration with TradingView

Moving averages can be used with Pine Script alerts:

```pinescript
// Pine Script example
fast_ema = ta.ema(close, 8)
slow_ema = ta.ema(close, 21)

if ta.crossover(fast_ema, slow_ema)
    alert("EMA Crossover: Bullish", alert.freq_once_per_bar)
```

The webhook handler will process these alerts and apply your moving average strategies.

## Performance Considerations

- **Real-time Calculation**: Moving averages are calculated on each tick
- **Memory Usage**: Rolling windows maintain price history
- **CPU Usage**: EMA calculations are optimized for speed
- **Accuracy**: All calculations use floating-point precision

## Troubleshooting

### Common Issues

1. **"Not enough data" errors**
   - Ensure sufficient price history is available
   - Check rolling window size vs. moving average period

2. **Incorrect crossover signals**
   - Verify EMA periods are appropriate
   - Check price data quality and frequency

3. **Performance issues**
   - Optimize rolling window size
   - Consider caching moving average values

### Debugging

Enable debug logging to see moving average calculations:

```python
import logging
logging.getLogger('backend.engine.strategy_evaluator').setLevel(logging.DEBUG)
```

This will show detailed information about moving average calculations and crossover detection. 