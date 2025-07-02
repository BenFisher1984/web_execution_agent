# Trade Persistence & Execution Recovery Plan

## Objective

Ensure that all open trades, stop logic, and execution state are safely recoverable in the event of application failure, system crash, or reboot. This complements the `API_connection_reliability_plan.md` and completes the high-availability strategy.

---

## 1. Persistent State Management

### ✅ What is Persisted:

* All trades, including:

  * `trade_status`
  * `order_status`
  * `filled_qty`, `fill_price`
  * `active_stop`, `initial_stop_price`, `trailing_stop_price`
  * `executed_price`, `calculated_quantity`
* Stored in `saved_trades.json`
* Automatically saved after any update (trigger, fill, stop activation, etc.)

### 🔁 Frequency:

* Every trade state update triggers an immediate overwrite of `saved_trades.json`
* Writes are synchronous (blocking) to ensure persistence

### 🛑 Failure Handling:

* If disk write fails, raise error and halt trading loop
* Ensure integrity of JSON via atomic write (e.g., temp file + rename)

---

## 2. Reboot Recovery Logic

### 🔄 On Application Startup:

* Load `saved_trades.json`
* For each trade:

  * If `trade_status = live` and `filled_qty` is present:

    * Resume `evaluate_trade_on_tick()`
    * Check `active_stop` conditions on first tick
  * If `trade_status = triggered` and `order_status = submitted`:

    * Optionally re-submit the entry order
    * Mark as stale if unfilled for > X minutes

---

## 3. Stop Loss & Exit Order Strategy

### 🧠 Stop Logic Source of Truth:

* Stops are **managed by the framework**, not pre-submitted to broker (soft stop model)

### 🔁 Live Monitoring:

* `evaluate_trade_on_tick()` checks `price <= active_stop.price`
* If breached:

  * Calls `order_executor.submit_exit_order()`
  * Marks trade as `closed`, sets `order_status = inactive`

### 🛡️ Optional: Hybrid Stop Mode

* Submit broker stop immediately after fill for failsafe
* On trailing stop update:

  * Cancel old IB stop, submit new one
* Ensures protection if system crashes

---

## 4. Watchdog & Process Health

### ⏱️ Runtime Monitoring:

* Tick handler emits heartbeat log every 5 sec: `"✅ Tick Engine Alive"`
* GUI displays last tick timestamp per trade
* Alert if >10 seconds since last tick for any live trade

### 🔁 Restart Strategy:

* Use `supervisord` or `systemd` to auto-restart app on crash
* Optional: Slack/email alert on restart event

---

## 5. Summary

This recovery plan ensures:

* Trade and stop state is persisted reliably
* Upon restart, no trade is left unmonitored
* Stops are always active (via framework or IB fallback)
* System uptime is guarded with watchdog monitoring

> Together with the API reliability plan, this provides production-grade resiliency against crashes, disconnections, and execution gaps.
