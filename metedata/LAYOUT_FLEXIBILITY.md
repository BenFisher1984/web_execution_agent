# 🧩 Layout Flexibility Requirements

## 🎯 Objective

To create a fully user-driven, metadata-configurable GUI layout where:

> **The layout the user defines is the layout that gets rendered.**
>
> No fields, labels, sections, dropdowns, or input behaviors are hardcoded.

---

## ✅ Design Goals

- The **GUI layout is defined entirely via `layout_config.json`**
- **Every field and section** in the execution cockpit must be:
  - Configurable
  - Extendable
  - Removable
  - Reorderable

---

## 🧠 What Must Be Configurable

| Element             | Description                                             | Configurable? |
|---------------------|---------------------------------------------------------|----------------|
| Field visibility     | Show/hide individual fields                             | ✅              |
| Field order          | Reorder fields within sections                          | ✅              |
| Section structure    | Add/remove/reorder sections                             | ✅              |
| Field labels         | Change display names (e.g. `ADR (50d)`)                 | ✅              |
| Input types          | Choose from: `text`, `number`, `checkbox`, `select`, `readonly` | ✅       |
| Dropdown options     | Define custom options per field                         | ✅              |
| Nested field support | e.g. `initial_stop_rule.price`                         | ✅              |
| Parameterized fields | e.g. `ATR (14d)` vs `ATR (21d)` via lookback            | ✅              |
| Volatility types     | `ADR`, `ATR`, `StDev`, `HV` — user chooses what & how   | ✅              |
| Future extensibility | Add new field types or config keys later                | ✅              |

---

## 🔄 Example Use Cases

- User wants to remove `Trailing Stop` fields — ✅ just omit them from the layout
- User wants `ADR (50d)` instead of `ADR (20d)` — ✅ configure a different lookback
- User wants new dropdown option `Limit (Post Only)` in `Order Type` — ✅ just edit the JSON
- User wants `Trade Status` to appear before `Symbol` — ✅ reorder fields in the config
- User wants to add a new section called `Pre-trade Checklist` — ✅ add a new section block

---

## 📁 Supporting File: `layout_config.json`

This single file drives:
- Field rendering
- Input widgets
- Dropdown logic
- Field/section layout

No JSX should hardcode layout logic — `App.js` simply renders what this config defines.

---

## 🧱 Architecture Enforcement

> **All layout changes must be made through config. No changes to `App.js` are allowed for layout modifications.**

This ensures:
- Maximum user flexibility
- No developer intervention required for layout changes
- Future GUI tools (layout builder) can safely edit this config

---

## 🛠 Status

✅ Agreed  
🚧 Next step: Generate full `layout_config.json` to replace current hardcoded structure
