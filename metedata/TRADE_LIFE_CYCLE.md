# Trade & Order Life Cycle (with Parent/Child OCO Framework)
_Last updated: 2025-07-04_

## Overview
This document outlines the complete life cycle of a trade and its associated orders in the broker-agnostic trading platform, explicitly incorporating the parent/child OCO (contingent order) framework. All orders—entry and contingent—are managed as virtual objects within the engine until their trigger is met. The broker is only ever aware of orders that are currently live in the market.

---

## Trade Statuses
- **-** (blank/null): No live order, no market risk.
- **Pending**: Trade is validated and working, waiting for entry condition and/or broker fill.
- **Filled**: Entry order filled, trade is live, market risk present.
- **Closed**: All positions/orders closed, no market risk.

## Order Statuses
- **Draft**: Order is being created/edited, not yet activated.
- **Working**: Order is validated and monitoring for trigger conditions (entry or contingent).
- **Entry Order Submitted**: Entry order sent to broker, awaiting fill confirmation.
- **Contingent Order Submitted**: Contingent (exit) order sent to broker, awaiting confirmation.
- **Contingent Order Working**: Contingent order accepted by broker, now live.
- **Inactive**: Order cancelled (by user or modification).
- **Cancelled**: Explicit user cancellation.
- **Rejected**: Broker rejected the order.
- **Pending (Virtual)**: (For child/contingent orders) Order is staged in the engine, waiting for parent fill or trigger condition.

---

## Order & Trade Statuses in Parent/Child OCO Context

### **Parent Order (Entry) Status Flow**
1. **Draft** → **Working** → **Entry Order Submitted** → **Filled** → **Inactive/Cancelled**

### **Child Orders (Contingent/Exit) Status Flow**
1. **Draft** → **Working** → **Pending (Virtual)** → **Contingent Order Submitted** → **Contingent Order Working** → **Filled/Inactive/Cancelled**

### **Trade Status Flow**
1. **-** → **Pending** → **Filled** → **Closed**

### **Status Relationships & Context**

| Trade Status | Parent Order Status | Child Order Status | Context |
|--------------|-------------------|-------------------|---------|
| **-** | Draft | Draft | Trade being created/edited |
| **Pending** | Working | Working/Pending (Virtual) | Trade activated, monitoring for triggers |
| **Pending** | Entry Order Submitted | Pending (Virtual) | Entry condition met, order sent to broker |
| **Filled** | Filled | Pending (Virtual) | Entry filled, contingent orders still virtual |
| **Filled** | Filled | Contingent Order Submitted | Contingent condition met, order sent to broker |
| **Filled** | Filled | Contingent Order Working | Contingent order accepted by broker |
| **Filled** | Filled | Filled/Inactive/Cancelled | Contingent order filled or cancelled |
| **Closed** | Inactive/Cancelled | Inactive/Cancelled | All orders closed, no market risk |

### **OCO Group Status Management**
- **Child orders in the same OCO group:**
  - When one child order is filled, all sibling orders in the OCO group are cancelled.
  - Status transitions: **Contingent Order Working** → **Cancelled** (for siblings).
  - Trade status remains **Filled** until all positions are closed.

### **Virtual vs. Live Order Tracking**
- **Virtual orders:** Stored in engine, not sent to broker (status: Draft, Working, Pending).
- **Live orders:** Transmitted to broker (status: Entry Order Submitted, Contingent Order Submitted, Contingent Order Working, Filled).
- **Engine responsibility:** Manage all virtual orders and their trigger conditions.
- **Broker responsibility:** Execute only live orders that have been transmitted.

---

## Life Cycle Steps (Parent/Child OCO Framework)

### 1. Trade & Virtual Order Creation
- User creates a trade (Draft).
- All orders (entry and contingent/child) are created and stored virtually in the engine.
- **Order Status:** Draft (all orders)
- **Trade Status:** -

### 2. Activate (Validation)
- User selects "Activate." Frontend does preliminary checks; backend performs full validation.
- **If validation fails:** Status unchanged.
- **If validation passes:**
  - **Order Status:** Working (all orders)
  - **Trade Status:** Pending
- *System is now monitoring for entry and contingent trigger conditions. No orders are sent to the broker yet.*

### 3. Entry Condition Met (Parent Order Triggered)
- When the entry condition is met:
  - **Entry Order Status:** Entry Order Submitted (transmitted to broker)
  - **Trade Status:** Pending
- *Only the entry order is sent to the broker at this point. All contingent (child) orders remain virtual (Pending/Working).* 

### 4. Entry Order Fill Confirmed by Broker
- When the broker confirms the entry order is filled:
  - **Entry Order Status:** Filled
  - **Trade Status:** Filled
  - **Child Orders Status:** Pending (Virtual) or Ready (now eligible for triggering)
- *Engine begins monitoring for contingent (exit) triggers. Child orders are still virtual.*

### 5. Contingent Condition Met (Child Order Triggered)
- When a contingent (child) order's trigger condition is met (e.g., price hits stop or target):
  - **Child Order Status:** Contingent Order Submitted (transmitted to broker)
  - **Trade Status:** Filled
- *Only the triggered child order is sent to the broker. Sibling child orders remain virtual until their own triggers or OCO logic applies.*

### 6. Contingent Order Fill & OCO Logic
- When a child order is filled by the broker:
  - **Child Order Status:** Contingent Order Working → Filled
  - **Trade Status:** Filled (until all positions/orders are closed)
  - **OCO Logic:** Engine cancels sibling child orders (if OCO group applies), updating their status to Cancelled/Inactive.
- *OCO (One Cancels Other) is managed by the engine. If one child order is filled, all others in the OCO group are cancelled locally and, if already live, at the broker.*

### 7. Trade Close
- When all positions/orders are closed:
  - **Order Status:** Inactive/Cancelled (all orders)
  - **Trade Status:** Closed
- *No market risk remains. All contingent logic is handled by the engine.*

### 8. Modification Workflow
- If user selects "Modify" on a live trade:
  - **Order Status:** Inactive (order is cancelled)
  - **Trade Status:** Filled (remains live, as there is still market risk)
- If user selects "Modify" on a trade that is not yet filled (e.g., Pending):
  - **Order Status:** Inactive (order is cancelled)
  - **Trade Status:** - (blank/null, as there is no live order and no market risk)
- *User must "Activate" again to re-validate and reactivate.*

### 9. Manual Cancel
- If user cancels an order:
  - **Order Status:** Cancelled
  - **Trade Status:**
    - If order was not filled: - (blank/null)
    - If order was filled and then cancelled/closed: Closed

### 10. Rejected
- If broker rejects an order:
  - **Order Status:** Rejected
  - **Trade Status:** - (unless trade was previously filled, then Closed)

---

## Parent/Child & OCO Relationships
- **Parent Order:** The entry order; only sent to broker when entry condition is met.
- **Child Orders:** Contingent (exit) orders (take profit, stop loss, trailing stop); only sent to broker when their trigger is met.
- **OCO Group:** Child orders can be grouped so that if one is filled, the others are cancelled by the engine (One Cancels Other logic).
- **All orders are virtual until their trigger is met.**

---

## Rationale & Notes
- The broker is only ever aware of orders that are currently live in the market.
- All parent/child/OCO logic is managed by the engine, not the broker, until orders are transmitted.
- Status transitions and OCO events are logged for audit and troubleshooting.
- This life cycle ensures reliability, transparency, and full auditability for both users and developers.

---

**This document should be referenced in all onboarding, code reviews, and major design decisions. Attach or paste this file to restore trade/order life cycle context for any future AI or developer.** 