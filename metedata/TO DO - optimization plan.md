# ⚙️ Optimization Plan — Tick Loop & API Throttling

This document outlines optimization strategies for ensuring the execution engine remains fast, scalable, and IB API-compliant under heavy load.

---

## ✅ Current Status

| Component         | Status       | Notes                                                       |
|------------------|--------------|-------------------------------------------------------------|
| Tick loop         | ✅ Optimized  | No blocking calls, logic preloaded                         |
| API interactions  | ✅ Safe       | Preload model avoids overload                              |
| Execution logic   | ✅ Modular    | Can scale with more trades or symbols                      |

---

## 🧠 Tick Loop Efficiency

### Risks When Scaling:
- Evaluating **every trade on every tick** wastes CPU
- Tick loop can stall if any operation is blocking or slow
- GUI may lag if backend is overloaded

### ✅ Recommendations:
- [ ] **Index trades by symbol** in `trade_manager` for direct access:
  ```python
  self.symbol_index = {"AAPL": [trade1, trade2], "TSLA": [trade3]}
