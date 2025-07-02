# backend/engine/take_profit_evaluator.py

import logging

logger = logging.getLogger(__name__)

class TakeProfitEvaluator:
    """
    Handles take-profit evaluation.
    """

    def evaluate_take_profit(self, trade: dict, price: float) -> dict:
        """
        Determines if the current price has triggered a take-profit.
        Returns a dict with:
          { 'triggered': bool, 'tp_price': float, 'tp_type': str }
        """
        tp_price = trade.get("take_profit_price")
        tp_type = trade.get("take_profit_type")
        direction = trade.get("direction", "Long")

        if tp_type in [None, "", "None"] or tp_price is None:
            return {"triggered": False, "tp_price": None, "tp_type": None}

        triggered = False
        if direction == "Long" and price >= tp_price:
            triggered = True
        elif direction == "Short" and price <= tp_price:
            triggered = True

        if triggered:
            logger.info(f"Take profit triggered: {direction} trade hit {tp_price} at current price {price}")
            return {"triggered": True, "tp_price": tp_price, "tp_type": tp_type}

        return {"triggered": False, "tp_price": tp_price, "tp_type": tp_type}
