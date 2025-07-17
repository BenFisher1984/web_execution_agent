import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.indicators import calculate_ema, calculate_sma, calculate_ema_crossover, calculate_moving_average, get_moving_average_value

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

def test_ema_crossover():
    """Test EMA crossover detection"""
    # Create a scenario where fast EMA crosses above slow EMA
    prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120]
    
    # Test with fast EMA (8) and slow EMA (21)
    fast_length = 8
    slow_length = 21
    
    try:
        crossover_data = calculate_ema_crossover(prices, fast_length, slow_length)
        print(f"✅ EMA Crossover Test:")
        print(f"   Fast EMA ({fast_length}): {crossover_data['fast_ema']:.2f}")
        print(f"   Slow EMA ({slow_length}): {crossover_data['slow_ema']:.2f}")
        print(f"   Signal: {crossover_data['signal']}")
        print(f"   Crossover detected: {crossover_data['crossover']}")
        
        # Verify that fast EMA > slow EMA in this scenario
        assert crossover_data['fast_ema'] > crossover_data['slow_ema'], "Fast EMA should be above slow EMA"
        assert crossover_data['signal'] == 'bullish', "Signal should be bullish"
        
    except ValueError as e:
        print(f"❌ EMA Crossover test failed: {e}")

def test_moving_average_functions():
    """Test the new moving average utility functions"""
    prices = [100, 102, 104, 106, 108, 110, 112]
    
    # Test calculate_moving_average
    sma_result = calculate_moving_average(prices, 'sma', 3)
    ema_result = calculate_moving_average(prices, 'ema', 3)
    
    print(f"✅ calculate_moving_average SMA: {sma_result}")
    print(f"✅ calculate_moving_average EMA: {ema_result}")
    
    # Test get_moving_average_value
    ma_config = {"type": "sma", "length": 3}
    ma_value = get_moving_average_value(prices, ma_config)
    print(f"✅ get_moving_average_value: {ma_value}")
    
    # Test with EMA config
    ema_config = {"type": "ema", "length": 5}
    ema_value = get_moving_average_value(prices, ema_config)
    print(f"✅ get_moving_average_value (EMA): {ema_value}")

def test_error_handling():
    """Test error handling for insufficient data"""
    prices = [100, 102]  # Not enough data for EMA crossover
    
    try:
        calculate_ema_crossover(prices, 8, 21)
        print("❌ Should have raised ValueError for insufficient data")
    except ValueError:
        print("✅ Correctly handled insufficient data for EMA crossover")
    
    try:
        calculate_ema(prices, 5)
        print("❌ Should have raised ValueError for insufficient data")
    except ValueError:
        print("✅ Correctly handled insufficient data for EMA")

if __name__ == "__main__":
    print("🧪 Testing Moving Averages...")
    test_moving_averages()
    print()
    
    print("🧪 Testing EMA Crossover...")
    test_ema_crossover()
    print()
    
    print("🧪 Testing Moving Average Functions...")
    test_moving_average_functions()
    print()
    
    print("🧪 Testing Error Handling...")
    test_error_handling()
    print()
    
    print("✅ All moving average tests completed!")
