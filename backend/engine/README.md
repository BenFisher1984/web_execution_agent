# Engine Module README

This folder (`backend/engine/`) contains the core logic for the execution agent. It interfaces with the Interactive Brokers (IBKR) API, handles volatility calculations, powers trade evaluation and status updates, and now includes a module for order submission (stubbed).

---

## 🧱 Module Overview

### `ib_client.py`
Handles all IBKR connectivity, contract resolution, last price retrieval (with fallback), historical data access, and real-time market data subscriptions.

Key Features:
- Connects to IB Gateway (port 4002)
- Retrieves contract details for any symbol (SMART/USD)
- Retrieves last price, falling back to close if needed
- Retrieves historical daily bars (OHLCV)
- **Subscribes to real-time tick data with callbacks**

Design Notes:
- Uses `math.isnan()` to avoid invalid price values
- 1-second sleep used to ensure ticker data is populated
- Returns `None` safely on failure with clear logging

---

### `volatility.py`
Provides volatility metrics for trade evaluation.

👍 Fully tested with live historical data using `test_volatility.py`.

Currently supports:
- ADR (Average Daily Range)
- ATR (Average True Range)

🛠️ Design Notes:
- User-defined `lookback` period supported via `options` dict
- Future fields (e.g., `basis`, `format`, `style`) can be added without changing function signatures
- Uses NumPy for vectorized operations and efficiency
- 🔁 Volatility metrics are now preloaded once at startup and reused during tick evaluation

---

### `trade_manager.py`
Evaluates trades loaded from `saved_trades.json`. Applies entry conditions and volatility checks, updates trade status, and persists trade state.

🔧 Current Features:
- Reads trades with user-defined entry conditions and lookbacks
- **Preloads ADR and ATR at startup and caches to each trade**
- Checks last price vs entry trigger using real-time data
- Uses cached ADR/ATR inside `evaluate_trade_on_tick()` — avoids repeated historical fetches
- Updates trade status and volatility fields if conditions are met
- **Now supports `evaluate_trade_on_tick(symbol, price)` for tick-based evaluation**
- Now supports `mark_trade_filled()` for post-entry fill tracking; SL/TP logic to follow
- **Now triggers `place_market_order(..., what_if=False)` during live runs**

🏛️ Design Notes:
- Modular and extensible structure
- Preloading volatility prevents event-loop conflicts
- Now supports both simulated and real (paper) orders
- Ready for injection of stop loss / trailing stop logic after fill

---

### `order_executor.py`
Responsible for submitting, modifying, and canceling orders via the IB Gateway.

✅ Current Implementation:
- `place_market_order(symbol, qty, what_if=True)` implemented with real/simulated toggle
- Supports fill monitoring using `monitor_order_fill()`
- Now supports **production-grade async-safe order fill monitoring**

🛠️ Design Notes:
- Retrieves contract via `ib_client`
- Uses `ib_insync.MarketOrder`
- Avoids `RuntimeError` by using `asyncio.create_task(...)`
- Uses `await asyncio.sleep(...)` inside `monitor_order_fill()` for non-blocking behavior
- Supports real paper orders during market hours, simulated ones during off-hours

Next methods: `place_limit_order()`, `place_bracket_order()`, `cancel_order()`

---

### `tick_handler.py`

### `validation.py`
Validates whether a trade contains all required fields to be activated.

📍 Located in: `backend/services/validation.py`

Key Responsibilities:
- Ensures required fields (e.g. symbol, direction, entry_trigger, stop rule) are present
- Enforces conditional logic (e.g. if trailing stop is enabled, rule must be defined)
- Returns a list of human-readable errors to inform GUI/UX logic

🧪 Tested via: `test_validation.py` in `backend/tests/`

---

### 🔄 Quantity & Stop Logic (New in trade_manager.py)

The `TradeManager` now supports:

- ✅ **Stop loss logic**: activated immediately upon fill, based on user-defined rule or custom price
- ✅ **Trailing stop logic**: optional, dynamically re-evaluated per tick, only one stop active at a time
- ✅ **Risk-based position sizing**: quantity is calculated from portfolio value × risk % ÷ stop distance
  - Uses `entry_trigger` as anchor for all sizing rules
  - Ensures precision even when filled quantity differs from calculated quantity

New module for real-time tick-based trade evaluation. Subscribes to tick data using `ib_client`, and triggers evaluations via `trade_manager`.

🔧 Current Features:
- `subscribe_to_symbols(symbols)` — subscribes to tick streams
- `on_tick()` — invoked on every tick to evaluate trades
- **Now supports defensive NaN check to skip invalid ticks**

🛠️ Design Notes:
- Fully decouples trade evaluation from polling logic
- Uses IBKR's `updateEvent` to receive tick data
- Replaces need for `scheduler.py` in production
- Now safe to run `evaluate_trade_on_tick()` on every tick due to preloaded volatility

---

## 🧪 Testing Notes

Use `backend/test_ib_connection.py` to manually test:
- `connect()` and `disconnect()`
- `get_contract_details(symbol)`
- `get_last_price(symbol)`
- `get_historical_data(symbol, lookback_days)`

Use `backend/test_volatility.py` to test:
- ADR and ATR calculation using live bar data
- Custom lookback values passed via options dict

Use `backend/test_trade_manager.py` to test:
- Trade evaluation loop using `saved_trades.json`
- Trigger logic and status update
- Volatility metrics recorded in trade
- **Preload logic for ADR/ATR now runs at startup**

Use `backend/test_subscribe_to_market_data.py` to test:
- Tick-based subscriptions using `subscribe_to_market_data()`
- Prints received ticks and validates callback

Use `backend/test_tick_handler.py` to test:
- Full real-time tick evaluation using `evaluate_trade_on_tick()`
- Confirms historical preload avoids async conflicts
- **Tick-triggered orders now call `place_market_order(..., what_if=...)`**
- **Supports real-time simulation OR live-paper execution**
- **Tested async-safe fill monitoring inside tick loop**

Use `backend/test_order_executor.py` to test:
- Safe simulated market order using `whatIf=True`
- Real order submission using `whatIf=False`
- Logs simulated or real margin impact if returned
- Verifies `monitor_order_fill()` works without `RuntimeError`

Each method prints results to console with clear pass/fail messaging.

---

## 🚣️ Future Improvements
- Add async support for concurrent requests
- Batch multiple tickers in one connection
- Move settings (e.g., RTH, fallback logic) into `settings.py`
- Expand volatility module with HV, StDev, raw ADR/ATR, etc.
- Build `order_executor.py` to handle live order placement and fill tracking
- Track portfolio exposure and risk limits in `portfolio.py`
- Replace `scheduler.py` with `tick_handler.py` in live runs
- Inject post-fill stop loss and trailing stop logic into `mark_trade_filled()`

---

### 🆕 Recent Updates (June 17, 2025)

#### ✅ Activation Tests Added
- New test file: `test_activation_pipeline.py` in `backend/tests/`
- Tests both successful and failed activation flows:
  - Valid trade → quantity calculated, status set to active
  - Invalid trade → returns error list
- Also prints the calculated quantity during test run for confirmation


#### ✅ Modular Position Sizing
- `calculate_position_size(trade)` has been extracted from `trade_manager.py`
- Now located in: `backend/services/activation_pipeline.py`
- Calculates quantity using risk %, portfolio value, and stop distance from entry trigger

#### ✅ New Activation Pipeline
- `activate_trade(trade)` introduced in `activation_pipeline.py`
- Runs `validate_trade(trade)` and, if valid:
  - Computes quantity
  - Sets `trade["quantity"]`
  - Sets `trade["status"] = "active"`
- Cleanly separates trade validation from activation & state mutation

#### ✅ GUI Logic Clarified
- Quantity is auto-calculated by frontend as soon as all required fields are valid
- No need to wait for trigger or manual activation to see estimated trade size
- `Order Status = Active` still required before execution eligibility

#### ✅ Architecture Discipline
- FastAPI reconfirmed as the backend API layer (not Flask)
- GUI/API integration to begin only after engine logic is fully production-ready

### 🧠 Tick-Based Active Stop Selection Logic

Once a trade is filled, the execution engine evaluates both the **initial stop loss** and (if present) the **trailing stop** on every tick.

#### ✅ Key Rules
- Exactly **one stop** can be active at any time.
- The **active stop** is stored in memory (not persisted to disk):
  ```python
  trade["active_stop"] = {"type": ..., "price": ...}


🆕 Recent Updates (June 18, 2025)
✅ Active Stop Selection Logic Fully Integrated
evaluate_trade_on_tick() now evaluates both pending and filled trades

Once a trade is filled, the engine dynamically selects the active stop:

If both stop_loss and trailing_stop["price"] are defined:

For long trades: the higher of the two becomes active

Only one stop can be active at a time

Stored as:

python
Copy
Edit
trade["active_stop"] = {"type": ..., "price": ...}
Not saved to disk — re-evaluated on every tick

✅ New Test: test_active_stop_selection.py
Simulates a filled trade and ticks

Verifies correct selection of trailing_stop or stop_loss based on current prices

✅ Test passes: trailing selected when higher; fallback to stop loss when lower

✅ Print statements now show:

Trade evaluation

Active stop selection:

arduino
Copy
Edit
📍 Active stop selected: trailing_stop @ $210.00
📍 Active stop selected: stop_loss @ $190.00
✅ Evaluate-Filled Logic Patch
Replaced unreachable if status != "pending": continue with a proper if/elif chain

Ensures "filled" trades are no longer skipped during tick evaluation



---

Maintained by: Software Engineer (GPT-4) and Entrepreneur (Ben)  
Status: ✅ MVP-ready and actively expanding
