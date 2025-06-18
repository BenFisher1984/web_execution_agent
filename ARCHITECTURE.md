## 🧠 Project Overview

This is a production-grade trading execution agent designed to run unattended during US market hours. It supports real-time tick-driven logic, flexible strategy definitions, risk management, and post-entry automation (e.g. stop loss, trailing stop, take profit). The project is built with long-term extensibility in mind, using a modular, metadata-driven architecture.

---

## 🏗️ Architecture Overview

```
web_execution_agent/
│
├── backend/
│   ├── engine/
│   │   ├── ib_client.py           # IBKR connection, contract and market data handling
│   │   ├── volatility.py          # Pre-session ADR/ATR calculations
│   │   ├── trade_manager.py       # Tick-by-tick evaluation of trades and state transitions
│   │   ├── order_executor.py      # Executes orders (whatIf + live) and tracks fills
│   │   └── tick_handler.py        # Subscribes to tick updates, routes to trade manager
│   ├── scheduler.py               # Optional: Time-based fallback loop
│   ├── config/
│   │   ├── layout_config.json     # GUI-driven layout metadata
│   │   └── saved_trades.json      # User-defined trades + state persistence
│   └── README.md                  # Developer reference
│
├── frontend/
│   └── react_app/                 # React + Tailwind GUI (to be integrated)
│
└── tests/                         # Test scripts for IB, volatility, ticks, execution
```

---

## ⚙️ Tech Stack

| Area                     | Chosen Tool(s)           | Notes                                                |
| ------------------------ | ------------------------ | ---------------------------------------------------- |
| **Execution Backend**    | `ib_insync`, `Python`    | Real-time API control over IB Gateway                |
| **Market Data**          | IBKR tick subscriptions  | Uses `IB.sleep` for async compatibility              |
| **GUI**                  | `React` + `Tailwind CSS` | Config-driven layout via `layout_config.json`        |
| **File Watch/Sync**      | Custom tick handler      | Event-driven, per-symbol logic                       |
| **Scheduler (fallback)** | `scheduler.py` loop      | Only for dev testing, not used in prod               |
| **Data Format**          | JSON                     | Flat user-defined config files                       |
| **Volatility Metrics**   | `NumPy` + `ib_insync`    | ADR and ATR, preloaded at session start              |
| **Testing Tools**        | Manual scripts, logging  | One script per module (e.g. `test_ib_connection.py`) |
| **Hosting (Future)**     | FastAPI + Uvicorn        | Will expose endpoints once GUI is wired in           |

---

## ✅ Key Design Principles

* **Tick-driven**: Each trade evaluates on every market tick using `IBKR` real-time data.
* **Strategy-Agnostic**: Users define trigger logic and constraints via `saved_trades.json`.
* **Post-Entry Logic**: Stop loss, trailing stop, take profit will be triggered after fills.
* **Volatility Preload**: No ADR/ATR calculated mid-session. Loaded once at start.
* **Readable & Extensible**: Clear module responsibilities, heavy use of docstrings.
* **No GUI Coupling**: Backend engine is fully decoupled from front-end logic.

✅ Final Confirmation
The engine must be real-time.
The GUI can lag if needed.

💡 Why this works:
The engine loop (tick handling, condition evaluation, execution) must be fast and isolated.

The GUI is just an interface for:

Inputting trades

Reviewing status

Triggering activation

GUI updates do not need to happen in real time — they can even be on a timer, manual refresh, or async poll.

🧱 What This Enables
Component	Priority	Sync Model
Tick loop	🚨 Highest	Real-time (in memory)
Trade activation	✅ High	API triggered
GUI view/update	😌 Flexible	Can be async or polled