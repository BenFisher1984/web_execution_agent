# API Connection Reliability Plan

## 🎯 Goals

* Maintain continuous connection to IB Gateway during market hours
* Automatically detect and recover from disconnection
* Prevent core engine from operating in a disconnected state
* Alert the user via GUI when connection is lost
* Gracefully handle expected disconnects during the daily reset window (e.g., 6:00pm Sydney)

---

## ✅ Features to Implement

### 1. Live Status Monitoring

* Use `ib.isConnected()` inside a background watchdog thread or async loop
* Poll every 1–5 seconds
* Write connection state to a shared `connection_status` variable

### 2. Auto-Reconnect

* Attempt reconnect using exponential backoff (e.g., 1s → 2s → 5s → 15s)
* Retry until connection succeeds
* Reset backoff on successful connection
* Suppress if disconnect occurs during reset window

### 3. GUI Alerting

* Current GUI polls `/status` — extend to:

  * Show warning banner or toast if API is down
  * Optionally disable activation / save buttons when disconnected
  * Display reconnect attempt status or countdown

### 4. Engine Guardrails

* All engine logic (tick evaluation, order execution) must check `ib.isConnected()`
* If disconnected:

  * Skip tick processing
  * Block order placements
  * Log safe warnings instead of erroring

### 5. Reset Window Awareness

* Backend reads `reset_time` and `timezone` from `settings.json`
* Suppress auto-reconnect and GUI alerting during that exact time window

### 6. Optional Enhancements (Future)

* Log all disconnects and reconnects to `connection_log.json`
* Track uptime/downtime % per day
* Display uptime stats in GUI footer
* Alert via email, webhook, or Slack

---

## ⏸ Status

🟨 Parked — planned for a future milestone. Safe to continue building other core features.

File created: 19-Jun-2025
