# 📡 External Signals Integration Framework (Planned)

## 🎯 Objective

Enable external trade signals (e.g. research provider alerts) to populate the GUI **automatically**, while maintaining the principle that:

> **The GUI is the user's source of truth. What appears in the table is what gets executed — nothing more, nothing less.**

---

## 🧩 Key Design Principles

- ✅ All trade data must appear in the GUI before reaching the backend
- ✅ No backend logic may update `saved_trades.json` without GUI awareness
- ✅ All external signals are **injected into the GUI first**
- ✅ User may review, edit, or discard signals before they are persisted or activated

---

## 🔄 Proposed Architecture Flow

```plaintext
[External Signal Source] (webhook, polling, email, etc.)
        ↓
[FastAPI Backend] receives and stores signals temporarily
        ↓
[GET /external_signals] REST endpoint returns queued signals
        ↓
[React GUI] polls this endpoint every 5–10 seconds
        ↓
[GUI State] injects new trades into the editable table
        ↓
[User] can modify, activate, or discard the trade
        ↓
[GUI] persists state to backend via POST /save_trades
        ↓
[saved_trades.json] updated via standard backend logic
