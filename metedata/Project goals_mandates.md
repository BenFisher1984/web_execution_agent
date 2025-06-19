# 🧠 Execution Agent Architecture Mandate

## 👤 Engineer Role

You are working with a **senior software engineer** with:

- Deep experience building **high-performance execution platforms**
- Expert knowledge of the **Interactive Brokers Gateway API**
- Proven ability to design **modular, scalable, and flexible architectures**
- Commitment to building production-grade systems from the ground up

---

## 🎯 Project Goal

Build a **real-time, multi-trade contingent order engine** where:

- ✅ Every tick triggers **fast**, **scalable**, and **conditional** logic
- ✅ System supports **multiple active trades** concurrently
- ✅ All logic must be **extensible** — able to evolve over time
- ✅ **Execution speed and reliability** are never compromised

---

## 🔐 Mandates — Non-Negotiable

### 1. **Protect the API**
- ⚠️ Any logic that **may overwhelm the IB API** (e.g. frequent redundant calls, inefficient loops, thread congestion) must be **flagged immediately**
- API stability is critical to real-time performance

### 2. **Enforce Future Flexibility**
- 🚫 Avoid **hardcoding symbols, field names, order logic, or layout assumptions**
- 🧩 Logic must always be **configurable** (via JSON or similar)
- ⛔ If I instruct hardcoded logic that prevents evolution, it **must be flagged**

### 3. **Modular Design**
- ♻️ Each component should operate independently and plug into the system
- ⚙️ Layouts, strategies, and rule sets must be **data-driven**
- 📐 New logic should be added **without modifying core behavior**

---

## ✅ Reminder

> **If either mandate is compromised, this program has no future.**
>  
> Your role is not only to build — but to **defend the architecture** at all times.
