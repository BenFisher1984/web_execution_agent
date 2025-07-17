# backend/engine/trailing_stop_evaluator.py

import logging
from typing import Dict, Any, Optional, Tuple
from .indicators import RollingWindow, calculate_ema, calculate_sma, get_moving_average_value

logger = logging.getLogger(__name__)

class TrailingStopEvaluator:
    """
    Handles trailing stop evaluation and updates. Enhanced for parent/child framework.
    Manages virtual trailing stops that are only sent to broker when triggered.
    """

    def should_update_trailing_stop(self, trade: dict, current_price: float,
                                  rolling_window: Optional[RollingWindow] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if trailing stop should be updated and calculate new stop level.
        
        Args:
            trade: Trade dictionary
            current_price: Current market price
            rolling_window: Rolling window for indicators
            
        Returns:
            Tuple[bool, dict]: (should_update, trailing_details)
        """
        trailing_rule = trade.get('trailing_stop_rules', [{}])[0]
        if not trailing_rule:
            return False, {"should_update": False, "reason": "No trailing rule"}
        
        # Check if we have sufficient data
        lookback = trailing_rule.get("parameters", {}).get("lookback", 20)
        if not rolling_window or len(rolling_window) < lookback:
            return False, {"should_update": False, "reason": "Insufficient data"}
        
        # Calculate new trailing stop
        new_trailing_stop = self._calculate_trailing_stop(trade, rolling_window)
        if new_trailing_stop is None:
            return False, {"should_update": False, "reason": "Calculation failed"}
        
        # Get current trailing stop
        current_trailing_stop = trade.get("current_trailing_stop")
        
        # Determine if update is needed
        should_update = self._should_update_stop(trade, current_trailing_stop, new_trailing_stop)
        
        trailing_details = {
            "should_update": should_update,
            "current_trailing_stop": current_trailing_stop,
            "new_trailing_stop": new_trailing_stop,
            "current_price": current_price,
            "direction": trade.get("direction", "Long")
        }
        
        if should_update:
            logger.info(f"Trailing stop update for {trade.get('symbol')}: "
                       f"{current_trailing_stop:.2f} → {new_trailing_stop:.2f}")
        
        return should_update, trailing_details

    def should_trigger_trailing_stop(self, trade: dict, current_price: float) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if trailing stop should be triggered (price hit trailing stop).
        
        Args:
            trade: Trade dictionary
            current_price: Current market price
            
        Returns:
            Tuple[bool, dict]: (triggered, trigger_details)
        """
        current_trailing_stop = trade.get("current_trailing_stop")
        if current_trailing_stop is None:
            return False, {"triggered": False, "reason": "No trailing stop active"}
        
        direction = trade.get("direction", "Long")
        triggered = False
        
        if direction == "Long":
            # For long positions, trigger if price falls below trailing stop
            triggered = current_price <= current_trailing_stop
        elif direction == "Short":
            # For short positions, trigger if price rises above trailing stop
            triggered = current_price >= current_trailing_stop
        else:
            logger.warning(f"Unknown direction: {direction}")
            return False, {"triggered": False, "reason": "Unknown direction"}
        
        trigger_details = {
            "triggered": triggered,
            "current_trailing_stop": current_trailing_stop,
            "current_price": current_price,
            "direction": direction
        }
        
        if triggered:
            logger.info(f"Trailing stop triggered for {trade.get('symbol')}: "
                       f"price {current_price:.2f} hit trailing stop {current_trailing_stop:.2f}")
        
        return triggered, trigger_details

    def _calculate_trailing_stop(self, trade: dict, 
                                rolling_window: RollingWindow) -> Optional[float]:
        """
        Calculate new trailing stop based on rule configuration.
        
        Args:
            trade: Trade dictionary with trailing rule
            rolling_window: Rolling window for indicators
            
        Returns:
            float: New trailing stop price or None if calculation fails
        """
        trailing_rule = trade.get('trailing_stop_rules', [{}])[0]
        if not trailing_rule:
            return None
        
        indicator = trailing_rule.get("indicator")
        params = trailing_rule.get("parameters", {})
        lookback = params.get("lookback", 20)
        offset = params.get("offset", 0.0)
        
        try:
            prices = rolling_window.get_window()
            
            if indicator == "ema":
                ema = calculate_ema(prices, lookback)
                trailing_stop = ema - offset
                logger.debug(f"Calculated EMA trailing stop: EMA({lookback}) = {ema:.2f}, "
                           f"trailing_stop = {trailing_stop:.2f}")
                return trailing_stop
                
            elif indicator == "sma":
                sma = calculate_sma(prices, lookback)
                trailing_stop = sma - offset
                logger.debug(f"Calculated SMA trailing stop: SMA({lookback}) = {sma:.2f}, "
                           f"trailing_stop = {trailing_stop:.2f}")
                return trailing_stop
                
            elif indicator == "custom_ma":
                ma_config = params.get("ma_config", {"type": "sma", "length": lookback})
                ma_value = get_moving_average_value(prices, ma_config)
                trailing_stop = ma_value - offset
                logger.debug(f"Calculated custom MA trailing stop: MA = {ma_value:.2f}, "
                           f"trailing_stop = {trailing_stop:.2f}")
                return trailing_stop
                
            elif indicator == "atr":
                # ATR-based trailing stop
                atr_period = params.get("atr_period", 14)
                atr_multiplier = params.get("atr_multiplier", 2.0)
                
                # Calculate ATR (simplified)
                if len(prices) >= atr_period:
                    high_low = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
                    atr = sum(high_low[-atr_period:]) / atr_period
                    trailing_stop = prices[-1] - (atr * atr_multiplier)
                    logger.debug(f"Calculated ATR trailing stop: ATR = {atr:.2f}, "
                               f"trailing_stop = {trailing_stop:.2f}")
                    return trailing_stop
                
            else:
                logger.warning(f"Unsupported trailing stop indicator: {indicator}")
                return None
                
        except Exception as e:
            logger.error(f"Error calculating trailing stop: {e}")
            return None

    def _should_update_stop(self, trade: dict, current_stop: Optional[float], 
                           new_stop: float) -> bool:
        """
        Determine if trailing stop should be updated based on direction and conservatism.
        
        Args:
            trade: Trade dictionary
            current_stop: Current trailing stop price
            new_stop: New calculated trailing stop price
            
        Returns:
            bool: True if stop should be updated
        """
        direction = trade.get("direction", "Long")
        
        # If no current stop, always update
        if current_stop is None:
            return True
        
        if direction == "Long":
            # For long positions, only update if new stop is higher (more conservative)
            return new_stop > current_stop
        elif direction == "Short":
            # For short positions, only update if new stop is lower (more conservative)
            return new_stop < current_stop
        else:
            logger.warning(f"Unknown direction: {direction}")
            return False

    def initialize_trailing_stop(self, trade: dict, rolling_window: RollingWindow) -> bool:
        """
        Initialize trailing stop for a trade (called when entry is filled).
        
        Args:
            trade: Trade dictionary
            rolling_window: Rolling window for indicators
            
        Returns:
            bool: True if initialization successful
        """
        trailing_rule = trade.get('trailing_stop_rules', [{}])[0]
        if not trailing_rule:
            return False
        
        initial_stop = self._calculate_trailing_stop(trade, rolling_window)
        if initial_stop is not None:
            trade["current_trailing_stop"] = initial_stop
            logger.info(f"Initialized trailing stop for {trade.get('symbol')}: {initial_stop:.2f}")
            return True
        
        return False

    def update_trailing_stop(self, trade: dict, new_stop: float) -> None:
        """
        Update the trailing stop in the trade.
        
        Args:
            trade: Trade dictionary
            new_stop: New trailing stop price
        """
        trade["current_trailing_stop"] = new_stop
        logger.debug(f"Updated trailing stop for {trade.get('symbol')}: {new_stop:.2f}")

    def get_trailing_stop_details(self, trade: dict) -> Dict[str, Any]:
        """
        Get trailing stop details for logging and debugging.
        
        Returns:
            dict: Trailing stop configuration
        """
        return {
            "trailing_stop_rule": trade.get('trailing_stop_rules', [{}])[0],
            "current_trailing_stop": trade.get("current_trailing_stop"),
            "direction": trade.get("direction", "Long")
        }

    def is_trailing_stop_active(self, trade: dict) -> bool:
        """
        Check if trailing stop is active for this trade.
        
        Args:
            trade: Trade dictionary
            
        Returns:
            bool: True if trailing stop is active
        """
        return (trade.get('trailing_stop_rules', [{}])[0] is not None and 
                trade.get("current_trailing_stop") is not None) 