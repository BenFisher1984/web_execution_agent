# API Connection Reliability Plan

## 🎯 Goals

* Maintain continuous connection to IB Gateway during market hours
* Automatically detect and recover from disconnection
* Prevent core engine from operating in a disconnected state
* Alert the user via GUI when connection is lost
* Gracefully handle expected disconnects during the daily reset window (e.g., 6:00pm Sydney)
* Ensure backend maintains persistent connection **independent of the frontend**
* GUI should remain optional — backend is the always-on engine

---

## ✅ Features to Implement

### 1. Live Status Monitoring

* Use `ib.isConnected()` inside a background watchdog thread or async loop
* Poll every 1–5 seconds
* Write connection state to a shared `connection_status` variable
* Run watchdog using `@app.on_event("startup")` or `asyncio.create_task(...)`

### 2. Auto-Reconnect

* Attempt reconnect using exponential backoff (e.g., 1s → 2s → 5s → 15s)
* Retry until connection succeeds
* Reset backoff on successful connection
* Suppress if disconnect occurs during reset window
* Implement reconnect logic in `ib_connection_manager.py` or similar service

### 3. GUI Alerting

* Current GUI polls `/status` — extend to:

  * Show warning banner or toast if API is down
  * Optionally disable activation / save buttons when disconnected
  * Display reconnect attempt status or countdown
* Optional: add "Connect to IB Gateway" button via POST `/connect_ib`

### 4. Engine Guardrails

* All engine logic (tick evaluation, order execution) must check `ib.isConnected()`
* If disconnected:

  * Skip tick processing
  * Block order placements
  * Log safe warnings instead of erroring

### 5. Reset Window Awareness

* Backend reads `reset_time` and `timezone` from `settings.json`
* Suppress auto-reconnect and GUI alerting during that exact time window
* Use `pytz` and `datetime.now(tz)` to determine current time in local timezone

### 6. Optional Enhancements (Future)

* Log all disconnects and reconnects to `connection_log.json`
* Track uptime/downtime % per day
* Display uptime stats in GUI footer
* Alert via email, webhook, or Slack

---

## 🔁 Production Behavior Expectations

| Event                           | Behavior                                               |
| ------------------------------- | ------------------------------------------------------ |
| Backend launches                | ✅ Auto-connect to IB Gateway                           |
| GUI closed or refreshed         | ✅ API connection persists                              |
| Gateway disconnects (non-reset) | ✅ Auto-reconnect loop triggers recovery                |
| Gateway resets (\~18:00 AEST)   | ✅ Reconnect suppressed during window, then resumes     |
| Manual button clicked in GUI    | ✅ Triggers `/connect_ib` if needed (optional fallback) |

---

## ⏸ Status

🟨 **Watchdog, reset suppression, and guardrails are planned but not yet implemented**
✅ Design is aligned with long-term production goals
