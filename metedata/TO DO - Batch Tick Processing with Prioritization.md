# 📄 Batch Tick Processing with Prioritization — Engineering Plan

## Background

Currently, the `TickHandler` processes each tick event individually, calling `TradeManager.evaluate_trade_on_tick` for every single tick. This is acceptable for low symbol counts, but will introduce event loop overhead and latency under high load (100s of symbols or multi-tenant SaaS).

**Goal:**  
- Collect ticks in short-time batches (e.g., 100–200 ms window)  
- Prioritize trades with tighter risk (e.g., distance-to-stop)  
- Dispatch trade evaluations based on priority  
- Support future scalability to hundreds of symbols with minimal latency

---

## File-by-File Implementation Plan

### 1️⃣ `tick_handler.py`

✅ Tasks:
- Refactor `process_tick_queue`:
  - Collect incoming ticks into a list/heap during a short batching window (e.g., `asyncio.sleep(0.1)`).
  - Process them as a batch instead of one-by-one.
- Introduce a **priority queue**:
  - Use `heapq` or similar.
  - Priority metric: absolute distance to active stop / last price (smaller = higher priority).
- Change `on_tick`:
  - Instead of enqueuing directly, push into a shared tick collection for batching.

✅ Outcome:
- Ticks are processed in groups.
- High-risk trades (near stops/targets) are evaluated first.
- Reduced event loop overhead.

---

### 2️⃣ `trade_manager.py`

✅ Tasks:
- Add helper:
  ```python
  def calculate_distance_to_stop(self, symbol, price) -> float:
      # returns normalized distance to current active stop
      # fallback to large number if no stop available
