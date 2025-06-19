# Web Execution Agent — Frontend (React + FastAPI)

This document outlines the structure, setup, and integration steps for the **React frontend** and its interaction with the **FastAPI backend**.

---

## 🧱 Project Structure

```
web_execution_agent/
├── backend/                # FastAPI server and trading engine
├── frontend/               # React app lives here
│   ├── react_app/          # React project root
│   └── README.md           # ← This file
└── saved_trades.json       # Trade data persisted to disk
```

---

## 🚀 Setup Instructions

### ✅ 1. Start the FastAPI Backend

```bash
cd web_execution_agent
uvicorn backend.app:app --reload
```

* Runs on: `http://localhost:8000`
* Serves trade data from `saved_trades.json`

---

### ✅ 2. Start the React Frontend

```bash
cd web_execution_agent/frontend/react_app
npm start
```

* Runs on: `http://localhost:3000` (or 3001 if already in use)
* Automatically fetches trade data from FastAPI

---

## 📊 GUI Table Layout (Live Trade Cockpit)

| Column            | Field                     | Editable | Source                  |
| ----------------- | ------------------------- | -------- | ----------------------- |
| Symbol            | `symbol`                  | ✅ Yes    | User-defined            |
| Trade Status      | `trade_status`            | ❌ No     | Engine-computed         |
| Order Status      | `order_status`            | ✅ Yes    | Toggle (active/pending) |
| Direction         | `direction`               | ✅ Yes    | Dropdown (buy/sell)     |
| Entry Trigger     | `entry_trigger`           | ✅ Yes    | Manual input            |
| Stop Type         | `initial_stop_rule.type`  | ✅ Yes    | Dropdown (custom)       |
| Stop Price        | `initial_stop_rule.price` | ✅ Yes    | Manual input            |
| Trailing Type     | `trailing_stop.type`      | ✅ Yes    | Dropdown (custom)       |
| Trailing Price    | `trailing_stop.price`     | ✅ Yes    | Manual input            |
| Portfolio Value   | `portfolio_value`         | ✅ Yes    | Manual input            |
| Risk %            | `risk_pct`                | ✅ Yes    | Manual input            |
| Quantity (Filled) | `filled_qty`              | ❌ No     | Engine-computed         |
| Order Type        | `order_type`              | ✅ Yes    | Dropdown                |
| Time in Force     | `time_in_force`           | ✅ Yes    | Dropdown (GTC, DAY)     |

---

## 🔁 Data Flow

1. **Page Load** → `GET /trades` from FastAPI
2. **User Edits Table** → React state updated in memory
3. (**Next**) User clicks **Save** → `POST /save_trades` to persist changes

---

## ⏭️ Next Steps

* Add "Save All" button to trigger `POST /save_trades`
* Integrate validation before order activation
* Add GUI feedback for validation errors

---

## ✅ Status Summary

* [x] FastAPI server operational
* [x] React app initialized and fetching trade data
* [x] GUI matches engine field naming convention
* [ ] Save button and data persistence (next)

---

## 📌 Notes

* Engine expects `initial_stop_rule` and `trailing_stop` to be objects with `type` and `price`
* No placeholder fields (`trail %`, `anchor`) remain in the table
* GUI speed is not critical — engine tick logic handles real-time processing

---

Created by Ben — 2025-06-18
