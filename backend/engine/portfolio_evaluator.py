# backend/engine/portfolio_evaluator.py

import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class PortfolioEvaluator:
    """
    Handles portfolio filters and risk conditions. Enhanced for parent/child framework.
    Evaluates portfolio constraints before allowing trade execution.
    """

    def should_allow_trade(self, trade: dict, portfolio_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate if a trade should be allowed based on portfolio constraints.
        
        Args:
            trade: Trade dictionary
            portfolio_data: Current portfolio data
            
        Returns:
            Tuple[bool, dict]: (allowed, evaluation_details)
        """
        # Check basic portfolio filters
        basic_check, basic_details = self._evaluate_basic_filters(trade, portfolio_data)
        if not basic_check:
            return False, basic_details
        
        # Check risk conditions
        risk_check, risk_details = self._evaluate_risk_conditions(trade, portfolio_data)
        if not risk_check:
            return False, risk_details
        
        # Check position limits
        position_check, position_details = self._evaluate_position_limits(trade, portfolio_data)
        if not position_check:
            return False, position_details
        
        return True, {
            "allowed": True,
            "basic_filters": basic_details,
            "risk_conditions": risk_details,
            "position_limits": position_details
        }

    def _evaluate_basic_filters(self, trade: dict, portfolio_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate basic portfolio filters (buying power, etc.).
        
        Args:
            trade: Trade dictionary
            portfolio_data: Portfolio data
            
        Returns:
            Tuple[bool, dict]: (passed, filter_details)
        """
        available_buying_power = portfolio_data.get("available_buying_power", 0)
        required_buying_power = self._calculate_required_buying_power(trade, portfolio_data)
        
        if required_buying_power > available_buying_power:
            return False, {
                "filter": "buying_power",
                "required": required_buying_power,
                "available": available_buying_power,
                "reason": "Insufficient buying power"
            }
        
        return True, {
            "filter": "buying_power",
            "required": required_buying_power,
            "available": available_buying_power,
            "passed": True
        }

    def _evaluate_risk_conditions(self, trade: dict, portfolio_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate risk conditions (max loss, sector exposure, etc.).
        
        Args:
            trade: Trade dictionary
            portfolio_data: Portfolio data
            
        Returns:
            Tuple[bool, dict]: (passed, risk_details)
        """
        # Check maximum loss per trade
        max_loss_per_trade = portfolio_data.get("max_loss_per_trade", float('inf'))
        potential_loss = self._calculate_potential_loss(trade, portfolio_data)
        
        if potential_loss > max_loss_per_trade:
            return False, {
                "condition": "max_loss_per_trade",
                "potential_loss": potential_loss,
                "max_allowed": max_loss_per_trade,
                "reason": "Potential loss exceeds maximum"
            }
        
        # Check maximum portfolio loss
        max_portfolio_loss = portfolio_data.get("max_portfolio_loss", float('inf'))
        current_portfolio_loss = portfolio_data.get("current_portfolio_loss", 0)
        
        if current_portfolio_loss + potential_loss > max_portfolio_loss:
            return False, {
                "condition": "max_portfolio_loss",
                "current_loss": current_portfolio_loss,
                "additional_loss": potential_loss,
                "max_allowed": max_portfolio_loss,
                "reason": "Would exceed maximum portfolio loss"
            }
        
        return True, {
            "condition": "risk_limits",
            "potential_loss": potential_loss,
            "current_portfolio_loss": current_portfolio_loss,
            "passed": True
        }

    def _evaluate_position_limits(self, trade: dict, portfolio_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate position size limits.
        
        Args:
            trade: Trade dictionary
            portfolio_data: Portfolio data
            
        Returns:
            Tuple[bool, dict]: (passed, position_details)
        """
        symbol = trade.get("symbol")
        trade_quantity = trade.get("quantity", 0)
        
        # Check maximum position size per symbol
        max_position_size = portfolio_data.get("max_position_size", float('inf'))
        current_position = portfolio_data.get("positions", {}).get(symbol, 0)
        
        if abs(current_position + trade_quantity) > max_position_size:
            return False, {
                "limit": "max_position_size",
                "current_position": current_position,
                "trade_quantity": trade_quantity,
                "max_allowed": max_position_size,
                "reason": "Would exceed maximum position size"
            }
        
        # Check maximum portfolio concentration
        max_concentration = portfolio_data.get("max_concentration", 1.0)  # 100%
        portfolio_value = portfolio_data.get("portfolio_value", 1)
        trade_value = trade_quantity * portfolio_data.get("current_price", 0)
        
        if trade_value / portfolio_value > max_concentration:
            return False, {
                "limit": "max_concentration",
                "trade_value": trade_value,
                "portfolio_value": portfolio_value,
                "concentration": trade_value / portfolio_value,
                "max_allowed": max_concentration,
                "reason": "Would exceed maximum concentration"
            }
        
        return True, {
            "limit": "position_limits",
            "current_position": current_position,
            "trade_quantity": trade_quantity,
            "passed": True
        }

    def _calculate_required_buying_power(self, trade: dict, portfolio_data: Dict[str, Any]) -> float:
        """
        Calculate required buying power for the trade.
        
        Args:
            trade: Trade dictionary
            portfolio_data: Portfolio data
            
        Returns:
            float: Required buying power
        """
        quantity = trade.get("quantity", 0)
        current_price = portfolio_data.get("current_price", 0)
        
        # Basic calculation: quantity * price
        required_power = quantity * current_price
        
        # Add margin requirements if applicable
        margin_requirement = portfolio_data.get("margin_requirement", 1.0)
        required_power *= margin_requirement
        
        return required_power

    def _calculate_potential_loss(self, trade: dict, portfolio_data: Dict[str, Any]) -> float:
        """
        Calculate potential loss for the trade.
        
        Args:
            trade: Trade dictionary
            portfolio_data: Portfolio data
            
        Returns:
            float: Potential loss
        """
        quantity = trade.get("quantity", 0)
        current_price = portfolio_data.get("current_price", 0)
        stop_price = trade.get("initial_stop_price")
        
        if stop_price is None:
            # If no stop, use a default risk percentage
            risk_percentage = portfolio_data.get("default_risk_percentage", 0.02)  # 2%
            return quantity * current_price * risk_percentage
        
        # Calculate loss based on stop price
        if trade.get("direction", "Long") == "Long":
            loss_per_share = current_price - stop_price
        else:
            loss_per_share = stop_price - current_price
        
        return abs(quantity * loss_per_share)

    def get_portfolio_details(self, trade: dict, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get portfolio evaluation details for logging and debugging.
        
        Args:
            trade: Trade dictionary
            portfolio_data: Portfolio data
            
        Returns:
            dict: Portfolio evaluation details
        """
        required_power = self._calculate_required_buying_power(trade, portfolio_data)
        potential_loss = self._calculate_potential_loss(trade, portfolio_data)
        
        return {
            "required_buying_power": required_power,
            "available_buying_power": portfolio_data.get("available_buying_power", 0),
            "potential_loss": potential_loss,
            "current_portfolio_loss": portfolio_data.get("current_portfolio_loss", 0),
            "portfolio_value": portfolio_data.get("portfolio_value", 0),
            "current_price": portfolio_data.get("current_price", 0)
        }

    def is_portfolio_filter_active(self, trade: dict) -> bool:
        """
        Check if portfolio filters are active for this trade.
        
        Args:
            trade: Trade dictionary
            
        Returns:
            bool: True if portfolio filters are active
        """
        # Check if any portfolio filters are configured
        return (trade.get("portfolio_filters") is not None or 
                trade.get("risk_conditions") is not None)

    def update_portfolio_data(self, portfolio_data: Dict[str, Any], 
                            trade: dict, fill_price: float, fill_quantity: int) -> Dict[str, Any]:
        """
        Update portfolio data after a trade fill.
        
        Args:
            portfolio_data: Current portfolio data
            trade: Trade dictionary
            fill_price: Fill price
            fill_quantity: Fill quantity
            
        Returns:
            dict: Updated portfolio data
        """
        updated_data = portfolio_data.copy()
        
        # Update buying power
        trade_value = fill_quantity * fill_price
        updated_data["available_buying_power"] -= trade_value
        
        # Update positions
        symbol = trade.get("symbol")
        current_position = updated_data.get("positions", {}).get(symbol, 0)
        if trade.get("direction", "Long") == "Long":
            new_position = current_position + fill_quantity
        else:
            new_position = current_position - fill_quantity
        
        if "positions" not in updated_data:
            updated_data["positions"] = {}
        updated_data["positions"][symbol] = new_position
        
        # Update portfolio value
        updated_data["portfolio_value"] += trade_value
        
        return updated_data 