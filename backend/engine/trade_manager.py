from backend.engine.ib_client import IBClient
from backend.engine.volatility import calculate_adr, calculate_atr
import json
import os
import math
import time
from datetime import datetime
import asyncio
import logging
from backend.config.status_enums import OrderStatus, TradeStatus
from .entry_evaluator import EntryEvaluator
from .stop_loss_evaluator import StopLossEvaluator
from .take_profit_evaluator import TakeProfitEvaluator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradeManager:
    def __init__(self, ib_client: IBClient, order_executor=None, config_path="backend/config/saved_trades.json", enable_tasks=True):
        self.ib = ib_client
        self.order_executor = order_executor
        self.config_path = config_path
        self.trades = self.load_trades()
        self.trade_index = {trade["symbol"]: trade for trade in self.trades if trade.get("symbol")}
        self.save_pending = False
        self.save_delay = 1.0
        self.entry_evaluator = EntryEvaluator()
        self.stop_loss_evaluator = StopLossEvaluator()
        self.take_profit_evaluator = TakeProfitEvaluator()
        self._debounce_task = None
        self._sync_task = None

    async def start(self):
        if self._debounce_task is None:
            self._debounce_task = asyncio.create_task(self.debounce_save())
        if self._sync_task is None:
            self._sync_task = asyncio.create_task(self.sync_with_broker())
        logger.info("TradeManager background tasks started")

    async def stop(self):
        if self._debounce_task:
            self._debounce_task.cancel()
            try:
                await self._debounce_task
            except asyncio.CancelledError:
                pass
            self._debounce_task = None

        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None

        logger.info("TradeManager background tasks stopped")
    


    def load_trades(self):
        for attempt in range(3):
            try:
                if not os.path.exists(self.config_path):
                    logger.warning(f"No trade file found at {self.config_path}")
                    return []
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load trades (attempt {attempt + 1}): {e}")
                if attempt < 2:
                    time.sleep(1)
        logger.error("Max retries reached for loading trades")
        return []

    async def debounce_save(self):
        while True:
            if self.save_pending:
                self._save_trades()
                self.save_pending = False
            await asyncio.sleep(self.save_delay)

    def _save_trades(self):
        serializable_trades = []
        for trade in self.trades:
            trade_copy = dict(trade)
            trade_copy.pop("contract", None)
            serializable_trades.append(trade_copy)
        try:
            with open(self.config_path + ".tmp", "w") as f:
                json.dump(serializable_trades, f, indent=2)
            os.replace(self.config_path + ".tmp", self.config_path)
            logger.debug("Trades saved to disk")
        except Exception as e:
            logger.error(f"Failed to save trades: {e}")

    def save_trades(self):
        self.save_pending = True

    async def sync_with_broker(self):
        try:
            positions = self.ib.ib.positions()
            for position in positions:
                symbol = position.contract.symbol
                trade = self.trade_index.get(symbol)
                if trade and trade.get("trade_status") in ["live", TradeStatus.LIVE.value]:
                    trade["filled_qty"] = position.position
                    trade["executed_price"] = position.avgCost
                    logger.info(f"Synced trade for {symbol} with broker position")
            self.save_trades()
        except asyncio.TimeoutError:
            logger.error("Timeout syncing positions with broker")
        except Exception as e:
            logger.error(f"Failed to sync positions: {e}")

    async def preload_contracts(self):
        symbols = [trade.get("symbol") for trade in self.trades if trade.get("symbol")]
        contracts = await self.ib.get_contract_details_batch(symbols)
        for trade in self.trades:
            symbol = trade.get("symbol")
            contract = contracts.get(symbol)
            if contract:
                trade["contract"] = contract
                logger.debug(f"Preloaded contract for {symbol}")
            else:
                logger.error(f"Could not preload contract for {symbol}")

    async def preload_volatility(self):
        logger.info("Preloading volatility...")
        for trade in self.trades:
            symbol = trade.get("symbol")
            if not symbol:
                logger.warning("Skipping trade with no symbol")
                continue
            if symbol in self.ib.volatility_cache and self.ib.volatility_cache[symbol].get("last_updated", 0) > datetime.now().timestamp() - 86400:
                cached = self.ib.volatility_cache[symbol]
                trade["volatility"] = {"adr": cached["adr"], "atr": cached["atr"]}
                logger.debug(f"Using cached volatility for {symbol}")
                continue
            try:
                lookback = 20
                bars = await self.ib.get_historical_data(symbol, lookback_days=lookback)
                if not bars:
                    logger.warning(f"No bars for {symbol}")
                    continue
                adr = calculate_adr(bars, options={"lookback": lookback})
                atr = calculate_atr(bars, options={"lookback": 14})
                if adr is not None and atr is not None:
                    self.ib.volatility_cache[symbol] = {
                        "adr": adr,
                        "atr": atr,
                        "last_updated": datetime.now().timestamp()
                    }
                    trade["volatility"] = {"adr": adr, "atr": atr}
                    logger.info(f"Cached volatility for {symbol}: ADR={adr}%, ATR={atr}%")
                else:
                    logger.warning(f"Partial or no volatility data for {symbol}: ADR={adr}, ATR={atr}")
            except Exception as e:
                logger.error(f"Failed to preload volatility for {symbol}: {e}")
        self.save_trades()

    async def evaluate_trades(self, rolling_window=None):
        for trade in self.trades:
            symbol = trade.get("symbol")
            order_status = trade.get("order_status", OrderStatus.INACTIVE.value)
            trade_status = trade.get("trade_status", TradeStatus.PENDING.value)

            try:
                if order_status == OrderStatus.ACTIVE.value and trade_status == TradeStatus.PENDING.value:
                    last_price = await self.ib.get_last_price(symbol)
                    if last_price is None:
                        continue

                    if self.entry_evaluator.evaluate_entry(trade, last_price):
                        trade["order_status"] = OrderStatus.ENTRY_ORDER_SUBMITTED.value
                        if self.order_executor and trade.get("quantity"):
                            contract = trade.get("contract")
                            await self.order_executor.place_market_order(
                                contract or symbol,
                                trade["quantity"],
                                trade=trade,
                                what_if=False
                            )   
                        self.save_trades()
                        continue

                if trade_status == TradeStatus.LIVE.value:
                    last_price = await self.ib.get_last_price(symbol)
                    if last_price is None:
                        continue

                    sl_result = self.stop_loss_evaluator.evaluate_stop(trade, last_price, rolling_window)
                    if sl_result["triggered"]:
                        trade["order_status"] = OrderStatus.CONTINGENT_ORDER_SUBMITTED.value
                        trade["trade_status"] = TradeStatus.LIVE.value
                        if self.order_executor:
                            await self.order_executor.submit_exit_order(
                                symbol,
                                trade.get("filled_qty"),
                                last_price,
                                trade
                            )
                        self.save_trades()
                        continue

                    tp_result = self.take_profit_evaluator.evaluate_take_profit(trade, last_price, rolling_window)
                    if tp_result["triggered"]:
                        trade["order_status"] = OrderStatus.CONTINGENT_ORDER_SUBMITTED.value
                        trade["trade_status"] = TradeStatus.LIVE.value
                        if self.order_executor:
                            await self.order_executor.submit_exit_order(
                                symbol,
                                trade.get("filled_qty"),
                                last_price,
                                trade
                            )
                        self.save_trades()
                        continue

            except Exception as e:
                logger.error(f"Error evaluating trade for {symbol}: {e}")

    async def evaluate_trade_on_tick(self, symbol: str, price: float, rolling_window=None):
        trade = self.trade_index.get(symbol)
        if not trade:
            return

        order_status = trade.get("order_status", OrderStatus.INACTIVE.value)
        trade_status = trade.get("trade_status", TradeStatus.PENDING.value)

        try:
            if order_status == OrderStatus.ACTIVE.value and trade_status == TradeStatus.PENDING.value:
                if self.entry_evaluator.evaluate_entry(trade, price):
                    trade["order_status"] = OrderStatus.ENTRY_ORDER_SUBMITTED.value
                    if self.order_executor and trade.get("quantity"):
                        contract = trade.get("contract")
                        await self.order_executor.place_market_order(
                            contract or symbol,
                            trade["quantity"],
                            trade=trade,
                            what_if=False
                        )
                    self.save_trades()
                    return

            if trade_status == TradeStatus.LIVE.value:
                sl_result = self.stop_loss_evaluator.evaluate_stop(trade, price, rolling_window)
                if sl_result["triggered"]:
                    trade["order_status"] = OrderStatus.CONTINGENT_ORDER_SUBMITTED.value
                    trade["trade_status"] = TradeStatus.LIVE.value
                    if self.order_executor:
                        await self.order_executor.submit_exit_order(
                            symbol,
                            trade.get("filled_qty"),
                            price,
                            trade
                        )
                    self.save_trades()
                    return

                tp_result = self.take_profit_evaluator.evaluate_take_profit(trade, price, rolling_window)
                if tp_result["triggered"]:
                    trade["order_status"] = OrderStatus.CONTINGENT_ORDER_SUBMITTED.value
                    trade["trade_status"] = TradeStatus.LIVE.value
                    if self.order_executor:
                        await self.order_executor.submit_exit_order(
                            symbol,
                            trade.get("filled_qty"),
                            price,
                            trade
                        )
                    self.save_trades()
                    return

                filled_price = trade.get("executed_price")
                filled_qty = trade.get("filled_qty") or trade.get("quantity")
                portfolio_value = self.load_portfolio_value()
                if filled_price is not None and filled_qty and portfolio_value:
                    direction = trade.get("direction", "Long")
                    delta = price - filled_price if direction == "Long" else filled_price - price
                    pnl_dollar = round(delta * int(filled_qty), 2)
                    pnl_percent = round((pnl_dollar / float(portfolio_value)) * 100, 2)
                    trade["pnl_dollar"] = pnl_dollar
                    trade["pnl_percent"] = pnl_percent

                self.save_trades()
        except Exception as e:
            logger.error(f"Error evaluating trade on tick for {symbol}: {e}")


    def load_portfolio_value(self):
        for attempt in range(3):
            try:
                with open("backend/config/portfolio_config.json", "r") as f:
                    portfolio_data = json.load(f)
                    return float(portfolio_data.get("portfolio_value", 0))
            except Exception as e:
                logger.error(f"Failed to load portfolio value (attempt {attempt + 1}): {e}")
                if attempt < 2:
                    time.sleep(1)
        logger.error("Max retries reached for portfolio config")
        return 0

    async def mark_trade_filled(self, symbol, fill_price, filled_qty):
        logger.info(f"Inside mark_trade_filled: {symbol}, {fill_price}, {filled_qty}")
        trade = self.trade_index.get(symbol)
        if not trade or "Submitted" not in trade.get("order_status", ""):
            logger.warning(f"No matching trade or incorrect status for {symbol}")
            return

        # Update basic trade details
        trade["filled_qty"] = filled_qty
        trade["executed_price"] = fill_price
        trade["filled_at"] = datetime.now().isoformat()
        trade["order_status"] = OrderStatus.CONTINGENT_ORDER_ACTIVE.value
        trade["trade_status"] = TradeStatus.LIVE.value

        # Call stop loss evaluator to determine active stop
        try:
            sl_result = self.stop_loss_evaluator.evaluate_stop(trade, fill_price, None)
            if sl_result and "active_stop" in sl_result:
                trade["active_stop"] = {
                    "type": sl_result.get("type", "static"),
                    "price": sl_result["active_stop"],
                }
            else:
                trade["active_stop"] = None
                logger.warning(f"No active stop set for {symbol} by stop_loss_evaluator")
        except Exception as e:
            logger.error(f"Error evaluating stop loss for {symbol}: {e}")
            trade["active_stop"] = None

        # Call take profit evaluator to determine active take profit
        try:
            tp_result = self.take_profit_evaluator.evaluate_take_profit(trade, fill_price)
            if tp_result and tp_result.get("tp_price") is not None:
                trade["active_tp"] = {
                    "type": tp_result.get("tp_type", "take_profit"),
                    "price": tp_result["tp_price"],
                }
            else:
                trade["active_tp"] = None
                logger.warning(f"No active take profit set for {symbol} by take_profit_evaluator")
        except Exception as e:
            logger.error(f"Error evaluating take profit for {symbol}: {e}")
            trade["active_tp"] = None

        # Optionally calculate initial risk metrics based on the active stop
        entry = trade.get("executed_price")
        qty = trade.get("filled_qty")
        stop = trade.get("active_stop", {}).get("price")
        portfolio_value = self.load_portfolio_value()

        if entry and stop and qty and portfolio_value:
            risk_per_share = abs(entry - stop)
            dollar_at_risk = qty * risk_per_share
            percent_at_risk = (dollar_at_risk / portfolio_value) * 100
            trade["dollar_at_risk"] = round(dollar_at_risk, 2)
            trade["percent_at_risk"] = round(percent_at_risk, 2)
            logger.info(
                f"Contingent orders set for {symbol}: Stop Loss=${stop}, Dollar Risk=${dollar_at_risk}, Percent Risk={percent_at_risk:.2f}%"
            )
        else:
            trade["dollar_at_risk"] = 0
            trade["percent_at_risk"] = 0

        # Save trade state after update
        self.save_trades()


    async def mark_trade_closed(self, symbol: str, exit_price: float, exit_qty: float):
        trade = self.trade_index.get(symbol)
        if not trade or trade.get("order_status") != OrderStatus.CONTINGENT_ORDER_SUBMITTED.value:
            logger.warning(f"No matching trade or incorrect status for {symbol}")
            return

        logger.info(f"Exit fill confirmed for {symbol} @ ${exit_price} for {exit_qty} shares")

        trade["order_status"] = OrderStatus.INACTIVE.value
        trade["trade_status"] = TradeStatus.CLOSED.value
        trade["closed_reason"] = "exit_fill"
        trade["closed_at"] = datetime.now().isoformat()
        trade["exit_price"] = exit_price
        trade["exit_qty"] = exit_qty

        # Optional: Clear active stops and take profits
        trade["active_stop"] = None
        trade["active_tp"] = None

        self.save_trades()

        logger.info(f"Trade {symbol} closed and saved to disk")
