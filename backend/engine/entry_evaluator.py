# backend/engine/entry_evaluator.py

import logging
from typing import Dict, Any, Optional
from .indicators import RollingWindow, calculate_ema_crossover, get_moving_average_value

logger = logging.getLogger(__name__)

class EntryEvaluator:
    """
    Handles entry evaluation including direction and rule-based conditions.
    Supports the rule structure: Primary Source | Condition | Secondary Source | Value
    """

    def should_trigger_entry(self, trade: dict, current_price: float, 
                           rolling_window: Optional[RollingWindow] = None) -> bool:
        """
        Evaluate if a trade should be activated based on entry conditions.
        
        Args:
            trade: Trade dictionary containing entry rules
            current_price: Current market price
            rolling_window: Optional rolling window for technical indicators
            
        Returns:
            bool: True if entry conditions are met
        """
        entry_rule_obj = trade.get('entry_rules', [{}])[0]
        entry_rule = entry_rule_obj.get('primary_source', 'Custom')
        entry_rule_price = entry_rule_obj.get('value')
        direction = trade.get("direction", "Long")

        # Fallback to legacy trigger
        if entry_rule_price is None:
            entry_rule_price = trade.get("entry_trigger")

        # Handle custom price-based entry
        if entry_rule == "Custom" and entry_rule_price is not None:
            return self._evaluate_price_condition(direction, current_price, entry_rule_price)
        
        # Handle rule-based entry conditions
        elif entry_rule != "Custom":
            return self._evaluate_rule_condition(trade, current_price, rolling_window)
        
        return False

    def _evaluate_price_condition(self, direction: str, current_price: float, 
                                threshold_price: float) -> bool:
        """
        Evaluate simple price-based entry condition.
        
        Args:
            direction: "Long" or "Short"
            current_price: Current market price
            threshold_price: Entry threshold price
            
        Returns:
            bool: True if condition is met
        """
        if direction == "Long":
            return current_price >= threshold_price
        elif direction == "Short":
            return current_price <= threshold_price
        else:
            logger.warning(f"Unknown direction: {direction}")
            return False

    def _evaluate_rule_condition(self, trade: dict, current_price: float,
                               rolling_window: Optional[RollingWindow] = None) -> bool:
        """
        Evaluate rule-based entry conditions.
        
        Args:
            trade: Trade dictionary with rule configuration
            current_price: Current market price
            rolling_window: Optional rolling window for indicators
            
        Returns:
            bool: True if rule conditions are met
        """
        entry_rule_obj = trade.get('entry_rules', [{}])[0]
        entry_rule = entry_rule_obj.get('primary_source', 'Custom')
        entry_rule_price = entry_rule_obj.get('value')
        
        if entry_rule == "EMA_CROSSOVER":
            return self._evaluate_ema_crossover(trade, current_price, rolling_window)
        elif entry_rule == "MOVING_AVERAGE_ABOVE":
            return self._evaluate_moving_average_above(trade, current_price, rolling_window)
        elif entry_rule == "MOVING_AVERAGE_BELOW":
            return self._evaluate_moving_average_below(trade, current_price, rolling_window)
        elif entry_rule == "PRICE_ABOVE":
            return self._evaluate_price_above(trade, current_price)
        elif entry_rule == "PRICE_BELOW":
            return self._evaluate_price_below(trade, current_price)
        else:
            logger.warning(f"Unknown entry rule: {entry_rule}")
            return False

    def _evaluate_ema_crossover(self, trade: dict, current_price: float,
                               rolling_window: Optional[RollingWindow] = None) -> bool:
        """
        Evaluate EMA crossover entry condition.
        """
        if not rolling_window or len(rolling_window) < 2:
            logger.warning("Insufficient data for EMA crossover evaluation")
            return False
        
        try:
            prices = rolling_window.get_window()
            fast_length = trade.get("ema_fast", 8)
            slow_length = trade.get("ema_slow", 21)
            required_signal = trade.get("ema_signal", "bullish")
            
            crossover_data = calculate_ema_crossover(prices, fast_length, slow_length)
            
            if crossover_data["crossover"] and crossover_data["signal"] == required_signal:
                logger.info(f"EMA crossover entry triggered: {crossover_data['signal']} "
                          f"(fast EMA: {crossover_data['fast_ema']:.2f}, "
                          f"slow EMA: {crossover_data['slow_ema']:.2f})")
                return True
                
        except ValueError as e:
            logger.warning(f"Error calculating EMA crossover: {e}")
        
        return False

    def _evaluate_moving_average_above(self, trade: dict, current_price: float,
                                     rolling_window: Optional[RollingWindow] = None) -> bool:
        """
        Evaluate moving average above entry condition.
        """
        if not rolling_window or len(rolling_window) < 1:
            logger.warning("Insufficient data for moving average evaluation")
            return False
        
        try:
            prices = rolling_window.get_window()
            ma_config = trade.get("ma_config", {"type": "sma", "length": 20})
            
            ma_value = get_moving_average_value(prices, ma_config)
            triggered = current_price > ma_value
            
            if triggered:
                logger.info(f"Moving average above entry triggered: "
                          f"price {current_price:.2f} > MA {ma_value:.2f}")
            
            return triggered
            
        except ValueError as e:
            logger.warning(f"Error calculating moving average: {e}")
            return False

    def _evaluate_moving_average_below(self, trade: dict, current_price: float,
                                     rolling_window: Optional[RollingWindow] = None) -> bool:
        """
        Evaluate moving average below entry condition.
        """
        if not rolling_window or len(rolling_window) < 1:
            logger.warning("Insufficient data for moving average evaluation")
            return False
        
        try:
            prices = rolling_window.get_window()
            ma_config = trade.get("ma_config", {"type": "sma", "length": 20})
            
            ma_value = get_moving_average_value(prices, ma_config)
            triggered = current_price < ma_value
            
            if triggered:
                logger.info(f"Moving average below entry triggered: "
                          f"price {current_price:.2f} < MA {ma_value:.2f}")
            
            return triggered
            
        except ValueError as e:
            logger.warning(f"Error calculating moving average: {e}")
            return False

    def _evaluate_price_above(self, trade: dict, current_price: float) -> bool:
        """
        Evaluate price above entry condition.
        """
        threshold = trade.get('entry_rules', [{}])[0].get('value')
        if threshold is None:
            return False
        
        triggered = current_price >= threshold
        if triggered:
            logger.info(f"Price above entry triggered: {current_price:.2f} >= {threshold:.2f}")
        
        return triggered

    def _evaluate_price_below(self, trade: dict, current_price: float) -> bool:
        """
        Evaluate price below entry condition.
        """
        threshold = trade.get('entry_rules', [{}])[0].get('value')
        if threshold is None:
            return False
        
        triggered = current_price < threshold
        if triggered:
            logger.info(f"Price below entry triggered: {current_price:.2f} < {threshold:.2f}")
        
        return triggered

    def get_entry_details(self, trade: dict) -> Dict[str, Any]:
        """
        Get entry rule details for logging and debugging.
        
        Returns:
            dict: Entry rule configuration
        """
        return {
            "entry_rule": trade.get('entry_rules', [{}])[0].get('primary_source', 'Custom'),
            "entry_rule_price": trade.get('entry_rules', [{}])[0].get('value'),
            "direction": trade.get("direction", "Long"),
            "ema_fast": trade.get("ema_fast"),
            "ema_slow": trade.get("ema_slow"),
            "ema_signal": trade.get("ema_signal"),
            "ma_config": trade.get("ma_config")
        }
