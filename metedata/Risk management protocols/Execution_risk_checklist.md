# Execution Risk Checklist

## Purpose

Summarize all known execution and infrastructure risks into one unified checklist. This serves as the post-functional milestone reference for system hardening and QA.

---

## ✅ Core Plans Implemented

| Area                   | Description                                             | Document                              |
| ---------------------- | ------------------------------------------------------- | ------------------------------------- |
| ✅ API Connectivity     | Reconnect logic, reset window handling, GUI alerts      | API\_connection\_reliability\_plan.md |
| ✅ Trade State Recovery | Persistent trade state, stop resumption, crash recovery | Trade\_Recovery\_Plan.md              |

---

## 🔁 Remaining Risks to Address (with Details)

### 🟠 Duplicate or Missed Order Submission

* [ ] Add submission lock/idempotency guard to prevent double order submission when price oscillates around entry trigger.
* [ ] Ensure each trade can only be triggered once until filled or cancelled.
* [ ] Reconcile fills using IB's `reqExecutions()` API to confirm if trade was actually executed in case of missed callback.

### 🟠 IB Sync Drift (State Mismatch)

* [ ] On app restart or reconnect, poll open trades and open orders from IB to rehydrate local state.
* [ ] Track all IB Order IDs for stop-loss or limit orders and confirm orderStatus callbacks.
* [ ] Handle desync scenarios (e.g., trade marked filled locally but no IB record).

### 🟠 Tick Data Corruption or Latency

* [ ] Validate each incoming tick: skip if `price is None`, `0`, or non-numeric.
* [ ] Add timestamp to each tick and ignore ticks that are too old or arrive out of sequence.
* [ ] Use debounce logic for triggers/stops: require confirmation from 2 consecutive ticks or delay for X ms.

### 🟠 Trade Size / Risk Integrity

* [ ] Add sanity check to verify `filled_qty * price` does not exceed max position size or user capital.
* [ ] Ensure risk\_pct aligns with user limits post-fill.
* [ ] Confirm all `live` trades have an `active_stop` set — flag if missing.

### 🟠 Time-based Fragility (DST, Restarts)

* [ ] Use UTC internally for all timestamps, including fill time, trigger time, stop activation.
* [ ] Avoid logic that relies on `date.today()` or server-local clock.
* [ ] Review log timestamps for consistency across timezones.

### 🟠 False or Premature Stop Triggers

* [ ] Add stop breach threshold (e.g., price must fall below stop by at least 0.1%) to prevent single-tick triggers.
* [ ] For trailing stops, ensure trailing logic doesn't activate and trigger on the same tick.
* [ ] Optionally confirm stop breach with a second tick before firing exit logic.

---

## 🟩 Optional Enhancements (For Production Hardening)

* [ ] Submit hard stop-loss order to IB immediately after fill as a failsafe (hybrid model).
* [ ] Add internal watchdog to restart stalled threads or detect non-responsive tick engine.
* [ ] Integrate alerts: Slack/email when crash occurs, trade fills but GUI is disconnected, or tick gap exceeds threshold.

---

## Usage

Use this checklist to:

* Guide your next dev sprints after core trade pipeline works
* Feed into QA planning and test automation
* Review system resiliency quarterly as scale or risk grows
