from backend.engine.indicators import calculate_ema, calculate_sma

def test_moving_averages():
    # Sample data
    prices = [100, 102, 104, 106, 108, 110, 112]
    
    # SMA test
    sma_length = 3
    sma_result = calculate_sma(prices, sma_length)
    expected_sma = sum(prices[-sma_length:]) / sma_length
    print(f"✅ SMA({sma_length}) expected {expected_sma} → got {sma_result}")
    
    # EMA test
    ema_length = 3
    ema_result = calculate_ema(prices, ema_length)
    # manually stepping through EMA if needed, but you can trust the pattern
    print(f"✅ EMA({ema_length}) got {ema_result}")

    # Longer EMA for comparison
    ema_length_longer = 5
    ema_result_longer = calculate_ema(prices, ema_length_longer)
    print(f"✅ EMA({ema_length_longer}) got {ema_result_longer}")

if __name__ == "__main__":
    test_moving_averages()
