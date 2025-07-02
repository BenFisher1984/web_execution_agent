from ib_insync import MarketOrder, Contract, StopOrder
from backend.engine.ib_client import IBClient
from backend.config.status_enums import OrderStatus, TradeStatus
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderExecutor:
    def __init__(self, ib_client: IBClient, trade_manager=None):
        self.ib = ib_client
        self.trade_manager = trade_manager
        self.active_orders = {}  # Map orderId to trade data
        self.ib.ib.orderStatusEvent += self.on_order_status

    def on_order_status(self, order, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        trade_data = self.active_orders.get(order.orderId)
        if not trade_data:
            logger.debug(f"No trade data found for orderId {order.orderId}")
            return
        trade = trade_data.get("trade")
        symbol = trade.get("symbol") if trade else "Unknown"
        logger.info(f"Order Status Update for {symbol}: {status} | Filled Qty: {filled} @ ${avgFillPrice:.2f}")
        try:
            if status in ("Filled", "Cancelled"):
                if trade and self.trade_manager:
                    if trade.get("order_status") == OrderStatus.CONTINGENT_ORDER_SUBMITTED.value:
                        logger.info(f"Calling mark_trade_closed for {symbol}")
                        # Schedule async call properly
                        asyncio.create_task(
                            self.trade_manager.mark_trade_closed(symbol, avgFillPrice, filled)
                        )
                    else:
                        logger.info(f"Calling mark_trade_filled for {symbol}")
                        # Similarly schedule mark_trade_filled if it is async
                        asyncio.create_task(
                            self.trade_manager.mark_trade_filled(symbol, avgFillPrice, filled)
                        )

                else:
                    logger.warning(f"Cannot update trade state for {symbol}: trade_manager or trade missing")
                # Clean up to prevent memory leaks
                del self.active_orders[order.orderId]
                # Unsubscribe to avoid repeated triggers (optional, as single handler is global)
                # self.ib.ib.orderStatusEvent -= self.on_order_status  # Not needed with global handler
        except Exception as e:
            logger.error(f"Error processing order status for {symbol}: {e}")

    async def place_market_order(self, contract_or_symbol, quantity: int, trade=None, what_if=True):
        try:
            if isinstance(contract_or_symbol, Contract):
                contract = contract_or_symbol
                symbol = contract.symbol
            else:
                symbol = contract_or_symbol
                contract = trade.get("contract") if trade and trade.get("contract") else await self.ib.get_contract_details(symbol)
                if not contract:
                    logger.error(f"Could not retrieve contract for {symbol}")
                    return None

            order = MarketOrder('BUY', quantity)
            order.tif = trade.get("time_in_force", "GTC")
            order.whatIf = what_if


            trade_result = self.ib.ib.placeOrder(contract, order)

            if what_if:
                logger.info(f"[Simulated] Market order placed for {quantity} shares of {symbol}")
            else:
                logger.info(f"Market order placed for {quantity} shares of {symbol}")
                self.active_orders[order.orderId] = {"trade_result": trade_result, "trade": trade}

            if hasattr(trade_result, "orderState") and trade_result.orderState:
                logger.info("IBKR What-If Response:")
                logger.info(f"  Init Margin: {trade_result.orderState.initMarginBefore}, "
                            f"Maint Margin: {trade_result.orderState.maintMarginBefore}")
            else:
                logger.warning("No margin data returned from IBKR (orderState not populated)")

            return trade_result
        except asyncio.TimeoutError:
            logger.error(f"Timeout placing market order for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Failed to place market order for {symbol}: {e}")
            return None

    async def submit_exit_order(self, symbol, quantity, price, trade=None):
        try:
            contract = trade.get("contract") if trade and trade.get("contract") else await self.ib.get_contract_details(symbol)
            if not contract:
                logger.error(f"Could not retrieve contract for {symbol}")
                return None

            direction = trade.get("direction") if trade else "Long"
            action = 'SELL' if direction == "Long" else 'BUY'
            order = MarketOrder(action, quantity)
            order.tif = trade.get("time_in_force", "GTC")


            trade_result = self.ib.ib.placeOrder(contract, order)

            logger.info(f"Exit order placed for {quantity} shares of {symbol} at ${price:.2f} ({action})")
            self.active_orders[order.orderId] = {"trade_result": trade_result, "trade": trade}
            return trade_result
        except asyncio.TimeoutError:
            logger.error(f"Timeout placing exit order for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Failed to place exit order for {symbol}: {e}")
            return None