# Additional Execution Risks & System Safeguards

## Purpose

To document known risk scenarios not yet fully covered by the core API disconnection and trade recovery plans. Once core functionality is complete, this document will guide testing and enhancement work to achieve full institutional-grade reliability.

---

## 1. Duplicate or Missed Order Submission

### Risk:

* Order may be submitted more than once due to repeated trigger ticks.
* Fill event may be missed due to transient process failure.

### Mitigation Plan:

* Add idempotency lock: mark trade as `submission_in_progress` once trigger is hit.
* Reconcile fill state using `ib.reqExecutions()` or order logs.

---

## 2. Out-of-Sync State with IB

### Risk:

* Trade shown as `live` in local app but never filled at broker.
* Stop marked as cancelled locally but still active at IB.

### Mitigation Plan:

* Poll IB regularly for open orders and executions.
* Confirm all stop cancels via `orderStatus` callback.
* Log and reconcile broker-side order states on restart.

---

## 3. Bad Market Data / Tick Latency

### Risk:

* IB may send `None`, 0, or out-of-order ticks.
* Price jump or stale data may falsely trigger trade or stop.

### Mitigation Plan:

* Validate tick integrity: skip if `price is None` or non-numeric.
* Use timestamp on tick to ignore delayed ticks.
* Optionally debounce triggers (e.g., require 2 ticks to confirm stop).

---

## 4. Position Sizing & Trade Exposure Errors

### Risk:

* Logic bug or manual input error leads to oversized trade.
* Trade goes live without a stop attached.

### Mitigation Plan:

* Recalculate and log `position_size = qty * fill_price` before every order.
* Audit all `live` trades for missing `active_stop`.
* Add global exposure cap across trades.

---

## 5. Clock Drift or Time-Related Bugs

### Risk:

* DST changes, reboots, or timezones cause logic errors.
* Daily revalidation or cutoff logic fails on clock skew.

### Mitigation Plan:

* Use UTC timestamps for all internal state.
* Avoid `datetime.today()` or local-relative comparisons.

---

## 6. False Stop-Loss Triggers

### Risk:

* Single tick dip triggers stop unnecessarily.
* Trailing stop activates and fires on same tick.

### Mitigation Plan:

* Add threshold filter (e.g. stop must be breached by >0.1%).
* Confirm breach with second tick before executing exit.
* Delay trailing stop activation until price exceeds anchor by X%.

---

## Next Steps

* Revisit this list after core execution pipeline is functional.
* Prioritize each mitigation based on capital at risk.
* Integrate key tests and alerts into QA and monitoring layers.
