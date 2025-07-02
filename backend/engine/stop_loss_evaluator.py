# backend/engine/stop_loss_evaluator.py

import logging
from backend.engine.indicators import calculate_ema, calculate_sma

logger = logging.getLogger(__name__)

class StopLossEvaluator:
    """
    Evaluates stop-loss conditions, supporting dynamic trailing stops
    like EMA, SMA, or static initial stops.
    """

    def evaluate_stop(self, trade: dict, current_price: float, rolling_window) -> dict:
        """
        rolling_window: RollingWindow object for the trade symbol.
        """
        static_stop = trade.get("initial_stop_price")
        trailing_rule = trade.get("trailing_stop_rule")
        dynamic_stop = None

        # calculate trailing stop if a rule is present
        if trailing_rule:
            indicator = trailing_rule.get("indicator")
            params = trailing_rule.get("parameters", {})
            lookback = params.get("lookback", 20)
            offset = params.get("offset", 0.0)

            logger.debug(f"parsed trailing rule: indicator={indicator}, lookback={lookback}, offset={offset}")

            prices = rolling_window.get_window()

            if len(prices) >= lookback:
                logger.debug(f"prices window OK (have {len(prices)}, need {lookback})")
                if indicator == "ema":
                    ema = calculate_ema(prices, lookback)
                    dynamic_stop = ema - offset
                    logger.debug(f"calculated EMA({lookback}) = {ema}, dynamic_stop = {dynamic_stop}")
                elif indicator == "sma":
                    sma = calculate_sma(prices, lookback)
                    dynamic_stop = sma - offset
                    logger.debug(f"calculated SMA({lookback}) = {sma}, dynamic_stop = {dynamic_stop}")
                else:
                    logger.warning(f"Unsupported trailing stop indicator: {indicator}")
            else:
                logger.warning(
                    f"Not enough prices for trailing rule on {trade.get('symbol')} "
                    f"(needed {lookback}, got {len(prices)})"
                )

        # determine active stop
        active_stop = None
        if static_stop is not None and dynamic_stop is not None:
            if trade["direction"] == "Long":
                active_stop = max(static_stop, dynamic_stop)
            else:
                active_stop = min(static_stop, dynamic_stop)
        elif static_stop is not None:
            active_stop = static_stop
        elif dynamic_stop is not None:
            active_stop = dynamic_stop

        # store active stop in trade
        trade["active_stop"] = {
            "type": indicator if dynamic_stop else "static",
            "price": active_stop
        }


        # trigger evaluation
        triggered = False
        if active_stop is not None:
            if trade["direction"] == "Long" and current_price <= active_stop:
                triggered = True
            elif trade["direction"] == "Short" and current_price >= active_stop:
                triggered = True

        return {
            "triggered": triggered,
            "active_stop": active_stop
        }
