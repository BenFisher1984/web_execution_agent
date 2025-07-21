# backend/engine/take_profit_evaluator.py

import logging
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)

class TakeProfitEvaluator:
    """
    Handles take-profit evaluation with support for multiple target levels.
    Enhanced for parent/child framework.
    """

    def should_trigger_take_profit(self, trade: dict, current_price: float) -> Tuple[bool, Dict[str, Any]]:
        """
        Determines if the current price has triggered a take-profit.
        Uses the same rule format as EntryEvaluator and StopLossEvaluator.
        
        Args:
            trade: Trade dictionary
            current_price: Current market price
            
        Returns:
            Tuple[bool, dict]: (triggered, take_profit_details)
        """
        direction = trade.get("direction", "Long")
        take_profit_rules = trade.get("take_profit_rules", [])
        
        if not take_profit_rules:
            return False, {"triggered": False, "rule": None, "current_price": current_price}
        
        # Use the first take profit rule (like other evaluators)
        rule = take_profit_rules[0]
        target_price_str = rule.get("value")
        condition = rule.get("condition", ">=")
        
        if not target_price_str:
            return False, {"triggered": False, "rule": rule, "current_price": current_price}
        
        try:
            target_price = float(target_price_str)
        except (ValueError, TypeError):
            logger.warning(f"Invalid take profit price: {target_price_str}")
            return False, {"triggered": False, "rule": rule, "current_price": current_price}
        
        # Evaluate the condition
        triggered = False
        if direction == "Long":
            if condition == ">=" and current_price >= target_price:
                triggered = True
            elif condition == ">" and current_price > target_price:
                triggered = True
        elif direction == "Short":
            if condition == "<=" and current_price <= target_price:
                triggered = True
            elif condition == "<" and current_price < target_price:
                triggered = True
        
        take_profit_details = {
            "triggered": triggered,
            "rule": rule,
            "target_price": target_price,
            "current_price": current_price,
            "direction": direction,
            "condition": condition
        }
        
        if triggered:
            logger.info(f"Take profit triggered for {trade.get('symbol')}: "
                       f"price {current_price:.2f} {condition} target {target_price:.2f}")
        
        return triggered, take_profit_details

    def _get_take_profit_targets(self, trade: dict) -> List[Dict[str, Any]]:
        """
        Get all take profit targets for the trade.
        
        Args:
            trade: Trade dictionary
            
        Returns:
            List[dict]: List of take profit targets
        """
        targets = []
        
        # Primary take profit target
        primary_tp = trade.get("take_profit_price")
        primary_tp_type = trade.get("take_profit_type")
        
        if primary_tp is not None and primary_tp_type not in [None, "", "None"]:
            targets.append({
                "price": primary_tp,
                "type": primary_tp_type,
                "quantity": trade.get("take_profit_quantity", trade.get("calculated_quantity", 0)),
                "level": "primary"
            })
        
        # Additional take profit targets (for partial exits)
        additional_targets = trade.get("additional_take_profits", [])
        for i, target in enumerate(additional_targets):
            if target.get("price") is not None:
                targets.append({
                    "price": target["price"],
                    "type": target.get("type", "percentage"),
                    "quantity": target.get("quantity", 0),
                    "level": f"secondary_{i+1}"
                })
        
        return targets

    def _evaluate_target(self, trade: dict, current_price: float, 
                        target: Dict[str, Any], direction: str) -> bool:
        """
        Evaluate if a specific take profit target should be triggered.
        
        Args:
            trade: Trade dictionary
            current_price: Current market price
            target: Target configuration
            direction: Trade direction
            
        Returns:
            bool: True if target should be triggered
        """
        target_price = target.get("price")
        if target_price is None:
            return False
        
        if direction == "Long":
            # For long positions, trigger if price rises above target
            return current_price >= target_price
        elif direction == "Short":
            # For short positions, trigger if price falls below target
            return current_price <= target_price
        else:
            logger.warning(f"Unknown direction: {direction}")
            return False

    def get_next_target(self, trade: dict, current_price: float) -> Optional[Dict[str, Any]]:
        """
        Get the next take profit target that hasn't been triggered yet.
        
        Args:
            trade: Trade dictionary
            current_price: Current market price
            
        Returns:
            dict: Next target or None if no targets remain
        """
        direction = trade.get("direction", "Long")
        targets = self._get_take_profit_targets(trade)
        
        if not targets:
            return None
        
        # Sort targets by price (ascending for longs, descending for shorts)
        if direction == "Long":
            targets.sort(key=lambda x: x["price"])
        else:
            targets.sort(key=lambda x: x["price"], reverse=True)
        
        # Find the next untriggered target
        for target in targets:
            if not self._evaluate_target(trade, current_price, target, direction):
                return target
        
        return None

    def get_take_profit_details(self, trade: dict) -> Dict[str, Any]:
        """
        Get take profit details for logging and debugging.
        
        Returns:
            dict: Take profit configuration
        """
        return {
            "take_profit_price": trade.get("take_profit_price"),
            "take_profit_type": trade.get("take_profit_type"),
            "take_profit_quantity": trade.get("take_profit_quantity"),
            "additional_take_profits": trade.get("additional_take_profits", []),
            "direction": trade.get("direction", "Long")
        }

    def is_take_profit_active(self, trade: dict) -> bool:
        """
        Check if take profit is active for this trade.
        
        Args:
            trade: Trade dictionary
            
        Returns:
            bool: True if take profit is active
        """
        return (trade.get("take_profit_price") is not None or 
                len(trade.get("additional_take_profits", [])) > 0 or
                len(trade.get("take_profit_rules", [])) > 0)

    def calculate_exit_quantity(self, trade: dict, target: Dict[str, Any]) -> int:
        """
        Calculate the quantity to exit for a specific target.
        
        Args:
            trade: Trade dictionary
            target: Target configuration
            
        Returns:
            int: Quantity to exit
        """
        filled_qty = trade.get("filled_qty", trade.get("calculated_quantity", 0))
        
        if target.get("type") == "percentage":
            # Percentage-based exit
            percentage = target.get("quantity", 0)
            return int((percentage / 100) * filled_qty)
        else:
            # Fixed quantity exit
            return int(target.get("quantity", filled_qty))

    def should_trigger_partial_exit(self, trade: dict, current_price: float) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a partial exit should be triggered (for multi-level targets).
        
        Args:
            trade: Trade dictionary
            current_price: Current market price
            
        Returns:
            Tuple[bool, dict]: (triggered, exit_details)
        """
        triggered, details = self.should_trigger_take_profit(trade, current_price)
        
        if not triggered:
            return False, details
        
        # Find the highest priority triggered target
        triggered_targets = details.get("triggered_targets", [])
        if not triggered_targets:
            return False, details
        
        # Sort by priority (primary first, then secondary)
        triggered_targets.sort(key=lambda x: x.get("level", "secondary"))
        target = triggered_targets[0]
        
        exit_quantity = self.calculate_exit_quantity(trade, target)
        
        exit_details = {
            "triggered": True,
            "target": target,
            "exit_quantity": exit_quantity,
            "current_price": current_price
        }
        
        return True, exit_details
