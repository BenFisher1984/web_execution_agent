from ib_insync import MarketOrder, Contract, StopOrder
from backend.engine.ib_client import IBClient
import asyncio  # ✅ For async sleep inside event loop


class OrderExecutor:
    def __init__(self, ib_client: IBClient, trade_manager=None):
        self.ib = ib_client
        self.trade_manager = trade_manager  # ✅ Optional injection for fill tracking

    def place_market_order(self, contract_or_symbol, quantity: int, trade=None, what_if=True):
        """
        Submit a market order for the given symbol or pre-qualified contract and quantity.
        This version uses 'whatIf=True' to simulate the order.

        If a Contract object is passed instead of a symbol, no lookup is performed.
        """
        if isinstance(contract_or_symbol, Contract):
            contract = contract_or_symbol
            symbol = contract.symbol
        else:
            symbol = contract_or_symbol
            contract = self.ib.get_contract_details(symbol)
            if not contract:
                print(f"❌ Could not retrieve contract for {symbol}")
                return None

        order = MarketOrder('BUY', quantity)
        order.whatIf = what_if  # ✅ Caller-controlled simulation flag

        trade_result = self.ib.ib.placeOrder(contract, order)

        if what_if:
            print(f"📥 [Simulated] Market order placed for {quantity} shares of {symbol}")
        else:
            print(f"📥 Market order placed for {quantity} shares of {symbol}")

        if hasattr(trade_result, "orderState") and trade_result.orderState:
            print("💡 IBKR What-If Response:")
            print(f"  Init Margin: {trade_result.orderState.initMarginBefore}, "
                  f"Maint Margin: {trade_result.orderState.maintMarginBefore}")
        else:
            print("⚠️ No margin data returned from IBKR (orderState not populated)")

        # ✅ Launch fill monitor safely in async loop
        if not order.whatIf:
            asyncio.create_task(self.monitor_order_fill(trade_result, contract, trade))

        return trade_result

    def place_stop_order(self, contract, quantity: int, stop_price: float, what_if=True):
        """
        Places a stop loss order for the given contract at the specified stop price.

        Args:
            contract: IBKR contract object
            quantity: number of shares to sell
            stop_price: the stop loss trigger price
            what_if: whether to simulate or actually submit the order
        """
        order = StopOrder('SELL', quantity, stopPrice=stop_price)
        order.whatIf = what_if

        self.ib.ib.placeOrder(contract, order)

        print(f"{'🧪 [Simulated]' if what_if else '📤'} Stop loss order placed for {contract.symbol} @ ${stop_price:.2f} for {quantity} shares")

    async def monitor_order_fill(self, trade_result, contract, trade):
        print(f"⏳ Monitoring fill status for order {contract.symbol}...")
        await asyncio.sleep(1)  # ✅ Async-safe delay

        while trade_result.orderStatus.status not in ('Filled', 'Cancelled'):
            await asyncio.sleep(1)
            self.ib.ib.reqOpenOrders()

        status = trade_result.orderStatus.status
        filled_qty = trade_result.orderStatus.filled
        avg_fill_price = trade_result.orderStatus.avgFillPrice

        print(f"✅ Order Status: {status} | Filled Qty: {filled_qty} @ ${avg_fill_price}")

        if status == 'Filled' and trade:
            symbol = trade.get("symbol")
            if self.trade_manager:
                print(f"📦 mark_trade_filled() will be called with: {symbol}, {avg_fill_price}, {filled_qty}")
                self.trade_manager.mark_trade_filled(symbol, avg_fill_price, filled_qty)

                # ✅ Call stop loss order immediately after fill
                stop_price = round(avg_fill_price * 0.98, 2)
                self.place_stop_order(contract, int(filled_qty), stop_price, what_if=False)
            else:
                print("❌ self.trade_manager is None — cannot mark trade as filled")
