
"""
trade_manager.py

Evaluates trades defined in saved_trades.json.
Applies entry conditions, volatility checks, and risk controls.
Will eventually manage trade state, order routing, and PnL tracking.
"""

from backend.engine.ib_client import IBClient
from backend.engine.volatility import calculate_adr, calculate_atr
import json
import os
import math

class TradeManager:
    def __init__(self, ib_client: IBClient, order_executor=None, config_path="backend/config/saved_trades.json"):
        self.ib = ib_client
        self.order_executor = order_executor  # ✅ Injected for execution wiring
        self.config_path = config_path
        self.trades = self.load_trades()
        self.preload_volatility()  # 🔁 Preload ADR/ATR once per session
        self.preload_contracts()    # 🔁 Preload contracts once per session

    def load_trades(self):
        """Loads saved trades from JSON config."""
        if not os.path.exists(self.config_path):
            print(f"⚠️ No trade file found at {self.config_path}")
            return []

        with open(self.config_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("❌ Error reading trade file — invalid JSON")
                return []

    def save_trades(self):
        """Writes the updated trade state back to JSON."""
        serializable_trades = []
        for trade in self.trades:
            trade_copy = dict(trade)
            if "contract" in trade_copy:
                del trade_copy["contract"]  # Exclude non-serializable contract object
            serializable_trades.append(trade_copy)

        with open(self.config_path, "w") as f:
            json.dump(serializable_trades, f, indent=2)

    def preload_volatility(self):
        """
        Preloads ADR and ATR for all trades once at startup.
        This ensures we do not fetch historical data during tick evaluation.
        """
        for trade in self.trades:
            symbol = trade.get("symbol")
            lookback = trade.get("lookback", 20)

            bars = self.ib.get_historical_data(symbol, lookback_days=lookback)
            if bars is None:
                print(f"⚠️ Could not load historical bars for {symbol} — skipping volatility preload.")
                continue

            adr = calculate_adr(bars, options={"lookback": lookback})
            atr = calculate_atr(bars, options={"lookback": 14})

            trade["volatility"] = {"adr": adr, "atr": atr}
            print(f"📊 Preloaded volatility for {symbol} — ADR: {adr}%, ATR: {atr}%")

        self.save_trades()

    def preload_contracts(self):
        """Preloads IBKR contracts for each trade and stores them for execution use."""
        for trade in self.trades:
            symbol = trade.get("symbol")
            contract = self.ib.get_contract_details(symbol)
            if contract:
                trade["contract"] = contract
            else:
                print(f"❌ Could not preload contract for {symbol}")

    def evaluate_trades(self):
        """Core evaluation loop. Checks each trade's conditions."""
        for trade in self.trades:
            symbol = trade.get("symbol")
            entry_trigger = trade.get("entry_trigger")
            order_status = trade.get("order_status", "pending")
            if order_status != "active":
                continue


            print(f"\n🔍 Evaluating {symbol}...")
            last_price = self.ib.get_last_price(symbol)
            if last_price is None:
                print(f"❌ No price data for {symbol}")
                continue

            vol = trade.get("volatility", {})
            adr = vol.get("adr")
            atr = vol.get("atr")

            print(f"📈 Last: ${last_price:.2f}, Entry Trigger: ${entry_trigger:.2f}, ADR: {adr}%, ATR: {atr}%")

            if last_price >= entry_trigger:
                print(f"✅ Entry triggered for {symbol}! (price >= {entry_trigger})")
                trade["trade_status"] = "triggered"
                trade["executed_price"] = last_price

        self.save_trades()

    def evaluate_trade_on_tick(self, symbol: str, price: float):
        """
        Evaluates all 'pending' trades for a given symbol using the live tick price.
        Relies on preloaded ADR/ATR, and does not make historical API calls.
        """
        updated = False

        for trade in self.trades:
            if trade.get("symbol") != symbol:
                continue

            order_status = trade.get("order_status", "pending")
            trade_status = trade.get("trade_status", "pending")

            if order_status == "active" and trade_status == "pending":
                entry_trigger = trade.get("entry_trigger")
                vol = trade.get("volatility", {})
                adr = vol.get("adr")
                atr = vol.get("atr")

                print(f"\n🔍 Evaluating {symbol} (tick-driven)...")
                if price is None:
                    print(f"❌ Tick price is None for {symbol}")
                    continue

                print(f"📈 Last: ${price:.2f}, Entry Trigger: ${entry_trigger:.2f}, ADR: {adr}%, ATR: {atr}%")

                if price >= entry_trigger:
                    print(f"✅ Entry triggered for {symbol}! (price >= {entry_trigger})")
                    trade["trade_status"] = "triggered"
                    trade["executed_price"] = price
                    updated = True

                    if self.order_executor:
                        contract = trade.get("contract")
                        if contract:
                            print(f"🧾 Passing trade to executor: {trade}")
                            qty = trade.get("quantity", 10)
                            self.order_executor.place_market_order(contract, quantity=qty, trade=trade, what_if=False)
                        else:
                            print(f"❌ No contract found for {symbol}, cannot place order.")

            elif trade_status == "filled":
                print(f"🛠 Evaluating filled trade: {symbol} @ ${price:.2f}")

                # 🧠 Tick-based active stop selection logic
                # At any point in time, exactly one stop must be considered "active":
                #   - If both stop_loss and trailing_stop["price"] are present:
                #       → Use the one closer to market (higher for long)
                #   - If only one is present, default to that
                #   - Never allow both to be active simultaneously
                #
                # The selected stop is stored in memory:
                #     trade["active_stop"] = {"type": ..., "price": ...}
                # This is NOT saved to disk — it is re-evaluated dynamically on every tick.

                stop_loss = trade.get("stop_loss")
                trailing = trade.get("trailing_stop", {})
                trailing_price = trailing.get("price")

                if trailing_price is not None and stop_loss is not None:
                    if trailing_price > stop_loss:
                        trade["active_stop"] = {"type": "trailing_stop", "price": trailing_price}
                    else:
                        trade["active_stop"] = {"type": "stop_loss", "price": stop_loss}

                elif stop_loss is not None:
                    trade["active_stop"] = {"type": "stop_loss", "price": stop_loss}

                elif trailing_price is not None:
                    trade["active_stop"] = {"type": "trailing_stop", "price": trailing_price}

                active_stop = trade.get("active_stop")
                if active_stop:
                    print(f"📍 Active stop selected: {active_stop['type']} @ ${active_stop['price']:.2f}")

        if updated:
            self.save_trades()


    def mark_trade_filled(self, symbol, fill_price, filled_qty):

        print(f"🧪 Inside mark_trade_filled(): {symbol}, {fill_price}, {filled_qty}")

        """
        Called once a market order is confirmed filled.
        Updates the trade state and triggers post-entry logic such as SL/TP.
        """
        for trade in self.trades:
            if trade.get("symbol") == symbol and trade.get("trade_status") == "triggered":
                trade["trade_status"] = "filled"

                trade["fill_price"] = fill_price
                trade["filled_qty"] = filled_qty
                print(f"🎯 Trade filled: {symbol} @ ${fill_price} for {filled_qty} shares")

                # 🚧 Placeholder for contingent orders (SL/TP/trailing)
                stop_loss_price = round(fill_price * 0.98, 2)  # 2% below fill
                trailing_stop = {
                    "trail_distance_pct": 2.0,
                    "anchor_price": fill_price
                }

                trade["stop_loss"] = stop_loss_price
                trade["trailing_stop"] = trailing_stop

                print(f"🧠 Contingent orders set for {symbol}:")
                print(f"   • Stop Loss: ${stop_loss_price}")
                print(f"   • Trailing Stop: 2% below new highs (anchored at ${fill_price})")

                self.save_trades()
                return
