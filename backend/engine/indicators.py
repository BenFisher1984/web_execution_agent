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


