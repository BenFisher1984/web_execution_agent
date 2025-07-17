Contingent Order Execution Framework (Replicating IB Bracket Style)
📌 Objective
Implement a parent/child contingent order engine with virtual child orders. The goal is to manage complex contingent logic (e.g., brackets, OCO, OTOCO) entirely within our engine, so that Interactive Brokers (IB) acts only as the execution venue. The IB broker will have no knowledge of child or contingent orders until they are explicitly activated and transmitted by our engine.

📌 Core Principles
Parent Order:

Transmitted immediately to IB for execution.

Represents the entry into the position.

Child Orders (profit targets, stop-loss):

Stored in our local order store as virtual orders.

Do not transmit these to IB until the parent order is fully or partially filled.

Mark them with status = pending in our system, referencing the parentOrderId.

Trigger Activation:

Once a fill event is detected on the parent order, the engine transitions the child orders to status = ready and transmits them to IB.

OCA / One Cancels All:

When child orders go live, group them logically with an ocaGroup identifier.

If one child is filled, your engine must automatically cancel the other child order.

This OCA logic is managed within our engine, not delegated to IB until orders are active.

Trailing Stop Logic:

Maintain trailing stops as a virtual price calculation on every tick price update.

Only transmit the stop order to IB once the calculated stop price is truly triggered.

No repeated cancel/replace at the broker; just one final execution.

📌 Flow Example (Bracket Order)
1️⃣ Submit Parent Order

e.g., Buy 100 AAPL @ $100

Transmit to IB immediately

Save child orders (take profit, stop loss) in local store with status = pending

2️⃣ Wait for Fill on Parent

Listen for IB order fill events on the parent

On full/partial fill, mark child orders status = ready

3️⃣ Activate Children

Transmit both child orders to IB (e.g., sell limit @ $110, stop-loss @ $95)

Group them with the same OCA group name (e.g., “BRACKET-1”)

Save them as status = active

4️⃣ OCA Handling

If the profit target fills, your engine must automatically cancel the stop-loss child

If the stop-loss fills, cancel the profit target child

IB may support OCA natively, but we should replicate this logic internally for consistency

📌 Architectural Responsibilities
✅ Engine responsibilities

Maintain local state of all parent/child orders

Maintain virtual trailing calculations

Coordinate activation of children

Handle OCA logic in a consistent way

Persist order statuses to database

✅ Broker responsibilities (IB)

Receive only actively transmitted orders

Execute them on the exchange

IB has no knowledge of any contingent structure until child orders are explicitly submitted

📌 Suggested Data Schema (simple draft)
json
Copy
Edit
{
  "orders": [
    {
      "orderId": 1,
      "symbol": "AAPL",
      "action": "BUY",
      "quantity": 100,
      "price": 100,
      "status": "transmitted",
      "parentId": null,
      "ocaGroup": null
    },
    {
      "orderId": 2,
      "symbol": "AAPL",
      "action": "SELL",
      "quantity": 100,
      "price": 110,
      "status": "pending",
      "parentId": 1,
      "ocaGroup": "BRACKET-1"
    },
    {
      "orderId": 3,
      "symbol": "AAPL",
      "action": "SELL",
      "quantity": 100,
      "stopPrice": 95,
      "status": "pending",
      "parentId": 1,
      "ocaGroup": "BRACKET-1"
    }
  ]
}
📌 Developer Tasks
✅ Build a parent/child order tracking module
✅ Implement a virtual contingent order manager (tick-based, rule-based engine)
✅ Implement an OCA manager within the engine
✅ Integrate IB API to listen to order fills and transmit child orders only after triggers
✅ Persist all order states to local database for recovery

📌 Design Notes
Our engine acts like a mini “order management server” just as IB does for bracket logic.

We intentionally hide child orders from IB until they are ready.

The user-facing experience is still “one bracket order” but behind the scenes, it is a staged and virtual structure.