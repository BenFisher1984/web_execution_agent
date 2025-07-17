# KEY PRINCIPLE: BROKER IS EXECUTION ONLY

---

## Absolute Architectural Rule

**The trading engine is the sole authority and manager of all order logic, state, and lifecycle.**

- The broker is **never** used for order staging, management, or OCO/OCA logic.
- **No order is ever live, pending, working, or staged at the broker.**
- The broker is only an execution endpoint: it receives a direct, immediate instruction to execute a market or limit order at the precise moment the engine decides.
- All order types—entry, stop loss, take profit, trailing stop, OCO/OCA—are managed 100% internally by the engine until the exact moment of execution.
- The broker never sees or manages any contingent, bracket, or virtual order logic.
- All OCO/OCA, trailing, and conditional logic is handled by the engine, not the broker.
- The only broker interaction is a direct, immediate execution command (e.g., "Buy 100 shares of XYZ now").

---

## Reference and Enforcement

- **This document must be referenced at the start of every chat or onboarding session.**
- Any design, code, or workflow that violates this principle is invalid and must be corrected immediately.
- If any response or implementation suggests broker-side order management, it is a mistake and must be called out and fixed.

---

**This is a non-negotiable, foundational rule for this trading platform.** 