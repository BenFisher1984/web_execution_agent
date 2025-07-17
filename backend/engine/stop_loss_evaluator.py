# backend/engine/stop_loss_evaluator.py

import logging
from typing import Dict, Any, Optional, Tuple
from .indicators import RollingWindow, calculate_ema, calculate_sma, get_moving_average_value

logger = logging.getLogger(__name__)

class StopLossEvaluator:
    """
    Evaluates stop-loss conditions, supporting dynamic trailing stops
    like EMA, SMA, or static initial stops. Enhanced for parent/child framework.
    """

    def should_trigger_stop(self, trade: dict, current_price: float, 
                           rolling_window: Optional[RollingWindow] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate if stop loss should be triggered.
        
        Args:
            trade: Trade dictionary
            current_price: Current market price
            rolling_window: Optional rolling window for indicators
            
        Returns:
            Tuple[bool, dict]: (triggered, stop_details)
        """
        direction = trade.get("direction", "Long")
        static_stop = trade.get("initial_stop_price")
        trailing_rule = trade.get('trailing_stop_rules', [{}])[0]
        
        # Calculate dynamic stop if trailing rule is present
        dynamic_stop = None
        if trailing_rule:
            dynamic_stop = self._calculate_dynamic_stop(trade, rolling_window)
        
        # Determine active stop (static vs dynamic)
        active_stop = self._determine_active_stop(trade, static_stop, dynamic_stop)
        
        # Store active stop in trade for reference
        if active_stop is not None:
            trade["active_stop"] = {
                "type": "dynamic" if dynamic_stop is not None else "static",
                "price": active_stop,
                "static_stop": static_stop,
                "dynamic_stop": dynamic_stop
            }
        
        # Evaluate trigger condition
        triggered = self._evaluate_stop_trigger(trade, current_price, active_stop)
        
        stop_details = {
            "triggered": triggered,
            "active_stop": active_stop,
            "stop_type": trade.get("active_stop", {}).get("type", "static"),
            "current_price": current_price,
            "direction": direction
        }
        
        if triggered:
            logger.info(f"Stop loss triggered for {trade.get('symbol')}: "
                       f"price {current_price:.2f} hit stop {active_stop:.2f}")
        
        return triggered, stop_details

    def _calculate_dynamic_stop(self, trade: dict, 
                               rolling_window: Optional[RollingWindow] = None) -> Optional[float]:
        """
        Calculate dynamic stop based on trailing rule.
        
        Args:
            trade: Trade dictionary with trailing rule
            rolling_window: Rolling window for indicators
            
        Returns:
            float: Dynamic stop price or None if calculation fails
        """
        trailing_rule = trade.get('trailing_stop_rules', [{}])[0]
        if not trailing_rule:
            return None
        
        indicator = trailing_rule.get("indicator")
        params = trailing_rule.get("parameters", {})
        lookback = params.get("lookback", 20)
        offset = params.get("offset", 0.0)
        
        if not rolling_window or len(rolling_window) < lookback:
            logger.warning(f"Insufficient data for dynamic stop calculation: "
                          f"need {lookback}, have {len(rolling_window) if rolling_window else 0}")
            return None
        
        try:
            prices = rolling_window.get_window()
            
            if indicator == "ema":
                ema = calculate_ema(prices, lookback)
                dynamic_stop = ema - offset
                logger.debug(f"Calculated EMA({lookback}) = {ema:.2f}, dynamic_stop = {dynamic_stop:.2f}")
                return dynamic_stop
                
            elif indicator == "sma":
                sma = calculate_sma(prices, lookback)
                dynamic_stop = sma - offset
                logger.debug(f"Calculated SMA({lookback}) = {sma:.2f}, dynamic_stop = {dynamic_stop:.2f}")
                return dynamic_stop
                
            elif indicator == "custom_ma":
                ma_config = params.get("ma_config", {"type": "sma", "length": lookback})
                ma_value = get_moving_average_value(prices, ma_config)
                dynamic_stop = ma_value - offset
                logger.debug(f"Calculated custom MA = {ma_value:.2f}, dynamic_stop = {dynamic_stop:.2f}")
                return dynamic_stop
                
            else:
                logger.warning(f"Unsupported trailing stop indicator: {indicator}")
                return None
                
        except Exception as e:
            logger.error(f"Error calculating dynamic stop: {e}")
            return None

    def _determine_active_stop(self, trade: dict, static_stop: Optional[float], 
                              dynamic_stop: Optional[float]) -> Optional[float]:
        """
        Determine which stop to use (static, dynamic, or combination).
        
        Args:
            trade: Trade dictionary
            static_stop: Static stop price
            dynamic_stop: Dynamic stop price
            
        Returns:
            float: Active stop price or None
        """
        direction = trade.get("direction", "Long")
        
        # If only static stop exists
        if static_stop is not None and dynamic_stop is None:
            return static_stop
        
        # If only dynamic stop exists
        elif static_stop is None and dynamic_stop is not None:
            return dynamic_stop
        
        # If both exist, use the more conservative one
        elif static_stop is not None and dynamic_stop is not None:
            if direction == "Long":
                # For long positions, use the higher stop (more conservative)
                active_stop = max(static_stop, dynamic_stop)
                logger.debug(f"Long position: static={static_stop:.2f}, dynamic={dynamic_stop:.2f}, "
                           f"active={active_stop:.2f}")
            else:
                # For short positions, use the lower stop (more conservative)
                active_stop = min(static_stop, dynamic_stop)
                logger.debug(f"Short position: static={static_stop:.2f}, dynamic={dynamic_stop:.2f}, "
                           f"active={active_stop:.2f}")
            return active_stop
        
        return None

    def _evaluate_stop_trigger(self, trade: dict, current_price: float, 
                              active_stop: Optional[float]) -> bool:
        """
        Evaluate if stop loss should be triggered.
        
        Args:
            trade: Trade dictionary
            current_price: Current market price
            active_stop: Active stop price
            
        Returns:
            bool: True if stop should be triggered
        """
        if active_stop is None:
            return False
        
        direction = trade.get("direction", "Long")
        
        if direction == "Long":
            # For long positions, trigger if price falls below stop
            return current_price <= active_stop
        elif direction == "Short":
            # For short positions, trigger if price rises above stop
            return current_price >= active_stop
        else:
            logger.warning(f"Unknown direction: {direction}")
            return False

    def should_update_trailing_stop(self, trade: dict, current_price: float,
                                  rolling_window: Optional[RollingWindow] = None) -> bool:
        """
        Check if trailing stop should be updated (for trailing stop logic).
        
        Args:
            trade: Trade dictionary
            current_price: Current market price
            rolling_window: Rolling window for indicators
            
        Returns:
            bool: True if trailing stop should be updated
        """
        trailing_rule = trade.get('trailing_stop_rules', [{}])[0]
        if not trailing_rule:
            return False
        
        # Only update if we have a trailing rule and sufficient data
        if rolling_window and len(rolling_window) >= trailing_rule.get("parameters", {}).get("lookback", 20):
            return True
        
        return False

    def get_stop_details(self, trade: dict) -> Dict[str, Any]:
        """
        Get stop loss details for logging and debugging.
        
        Returns:
            dict: Stop loss configuration
        """
        return {
            "initial_stop_price": trade.get("initial_stop_price"),
            "trailing_stop_rule": trade.get('trailing_stop_rules', [{}])[0],
            "active_stop": trade.get("active_stop", {}),
            "direction": trade.get("direction", "Long")
        }

    def is_stop_active(self, trade: dict) -> bool:
        """
        Check if stop loss is active for this trade.
        
        Args:
            trade: Trade dictionary
            
        Returns:
            bool: True if stop loss is active
        """
        return (trade.get("initial_stop_price") is not None or 
                trade.get('trailing_stop_rules', [{}])[0] is not None)
