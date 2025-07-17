from collections import deque

class RollingWindow:
    def __init__(self, length):
        self.length = length
        self.data = deque(maxlen=length)

    def preload(self, values):
        """
        Load initial historical values. Should be <= length.
        """
        for v in values:
            self.data.append(v)

    def append(self, new_value):
        """
        Add a new tick price to the rolling window.
        """
        self.data.append(new_value)

    def get_window(self):
        """
        Returns the current window as a list.
        """
        return list(self.data)

    def __len__(self):
        return len(self.data)
    
def calculate_ema(prices: list[float], length: int) -> float:
    """
    Calculate an EMA from the provided price list.
    Assumes prices are ordered oldest to newest.
    """
    if len(prices) < length:
        raise ValueError(f"Not enough prices to calculate {length}-period EMA")
    
    k = 2 / (length + 1)
    ema = sum(prices[:length]) / length  # start with simple average as seed
    
    for price in prices[length:]:
        ema = (price * k) + (ema * (1 - k))
    
    return ema
    
def calculate_sma(prices: list[float], length: int) -> float:
    """
    Calculate a simple moving average from the price list.
    """
    if len(prices) < length:
        raise ValueError(f"Not enough prices to calculate {length}-period SMA")
    
    return sum(prices[-length:]) / length

def calculate_ema_crossover(prices: list[float], fast_length: int, slow_length: int) -> dict:
    """
    Calculate EMA crossover signal.
    Returns dict with:
    - crossover: True if crossover detected
    - signal: 'bullish' if fast EMA > slow EMA, 'bearish' if fast EMA < slow EMA
    - fast_ema: current fast EMA value
    - slow_ema: current slow EMA value
    """
    if len(prices) < max(fast_length, slow_length):
        raise ValueError(f"Not enough prices for EMA crossover calculation")
    
    fast_ema = calculate_ema(prices, fast_length)
    slow_ema = calculate_ema(prices, slow_length)
    
    # Determine current signal
    current_signal = 'bullish' if fast_ema > slow_ema else 'bearish'
    
    # Check for crossover by comparing with previous values
    # We need at least one more data point to detect crossover
    if len(prices) >= max(fast_length, slow_length) + 1:
        prev_prices = prices[:-1]
        prev_fast_ema = calculate_ema(prev_prices, fast_length)
        prev_slow_ema = calculate_ema(prev_prices, slow_length)
        
        prev_signal = 'bullish' if prev_fast_ema > prev_slow_ema else 'bearish'
        
        # Crossover detected if signal changed
        crossover = current_signal != prev_signal
    else:
        crossover = False
    
    return {
        'crossover': crossover,
        'signal': current_signal,
        'fast_ema': fast_ema,
        'slow_ema': slow_ema,
        'fast_length': fast_length,
        'slow_length': slow_length
    }

def calculate_moving_average(prices: list[float], ma_type: str, length: int) -> float:
    """
    Calculate moving average by type.
    
    Args:
        prices: List of prices (oldest to newest)
        ma_type: 'sma' or 'ema'
        length: Period length
    
    Returns:
        Moving average value
    """
    if ma_type.lower() == 'sma':
        return calculate_sma(prices, length)
    elif ma_type.lower() == 'ema':
        return calculate_ema(prices, length)
    else:
        raise ValueError(f"Unsupported moving average type: {ma_type}")

def get_moving_average_value(prices: list[float], ma_config: dict) -> float:
    """
    Get moving average value based on configuration.
    
    Args:
        prices: List of prices
        ma_config: Dict with 'type' ('sma' or 'ema') and 'length'
    
    Returns:
        Moving average value
    """
    ma_type = ma_config.get('type', 'sma')
    length = ma_config.get('length', 20)
    
    return calculate_moving_average(prices, ma_type, length)


