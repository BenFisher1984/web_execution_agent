# ✅ New Thread Sync Checklist – Web-based Execution Agent

> Use this checklist any time you start a new thread within the project to ensure full file memory and architectural continuity.

---

## 🏗️ 1. Project Metadata

| File                 | Purpose                                                  |
| -------------------- | -------------------------------------------------------- |
| `ARCHITECTURE.md`    | Confirms architecture, tech stack, async design patterns |
| `README.md`          | Captures module-level summaries and current logic state  |
| `file_structure.txt` | Validates directory layout and confirms file presence    |

---

## ⚙️ 2. Core Engine Logic

| File                | Purpose                                                 |
| ------------------- | ------------------------------------------------------- |
| `ib_client.py`      | Market data, contract lookup, historical bars           |
| `order_executor.py` | Real/simulated order placement and async fill tracking  |
| `trade_manager.py`  | Tick/price-driven logic and post-fill evaluation        |
| `tick_handler.py`   | Tick subscription loop with NaN protection              |
| `volatility.py`     | Computes ADR/ATR using configurable lookback            |
| `app.py`            | FastAPI app entry point — bridges GUI ↔️ backend engine |

---

## 🧪 3. Test Scripts

| File                               | Purpose                                         |
| ---------------------------------- | ----------------------------------------------- |
| `test_ib_connection.py`            | Validates IBKR connection + basic contract/data |
| `test_order_executor.py`           | Simulated vs. real order execution              |
| `test_tick_handler.py`             | End-to-end trigger and tick testing             |
| `test_trade_manager.py`            | Static evaluation of all trades                 |
| `test_volatility.py`               | ADR/ATR calculations                            |
| `test_mark_trade_filled.py`        | Unit test of trade fill update logic            |
| `test_activation_pipeline.py`      | Validates position sizing and entry logic       |
| `test_active_stop_selection.py`    | Tests active stop logic at runtime              |
| `test_subscribe_to_market_data.py` | Tests subscription tick loop                    |
| `test_validation.py`               | Validation of trade objects and inputs          |

---

## ⚙️ 4. Config Files

| File                 | Purpose                                          |
| -------------------- | ------------------------------------------------ |
| `saved_trades.json`  | Source of all trades — must be up to date        |
| `layout_config.json` | UI layout placeholder (JSON-driven)              |
| `settings.py`        | Optional: toggle constants / environment configs |

---

## 🖥️ 5. Frontend (React GUI)

| File                              | Purpose                                             |
| --------------------------------- | --------------------------------------------------- |
| `frontend/react_app/App.js`       | Main React component rendering editable trade table |
| `frontend/react_app/package.json` | React dependencies and scripts                      |
| `frontend/react_app/README.md`    | FastAPI and React integration guide (new)           |

---

## ✅ Notes

* Upload **all files** in the new thread to avoid memory loss
* After upload, wait for confirmation of full sync
* Never assume project memory carries over between threads without re-upload

---

*Maintained by: GPT-4 + Ben, June 2025*
