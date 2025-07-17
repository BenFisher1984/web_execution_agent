# Migration: Trade Rule Types to Arrays (Frontend & Backend)

## Context
We undertook a comprehensive refactor of a trading application to migrate all trade rule types from singular object form to array form. This affects **entry rules, initial stop rules, trailing stop rules, and take profit rules**. The goal was to ensure that everywhere in the codebase, these rules are represented as arrays (e.g., `entry_rules`, `initial_stop_rules`, etc.), with all code, config, data, and tests updated accordingly.

---

## Key Migration Steps and Files Updated

### 1. Schema and Config
- **backend/schemas/trade_schema.json**
  - Changed `entry_rule` and `initial_stop_rule` from objects to arrays (`entry_rules`, `initial_stop_rules`).
  - Ensured all rule types are arrays in the schema.

- **backend/config/layout_config.json**
  - Updated all field keys for rule types to use array notation (e.g., `entry_rules.0.value`, `trailing_stop_rules.0.value`).

- **backend/config/saved_trades.json**
  - Migrated all trade data to use arrays for all rule types.

---

### 2. Frontend Code
- **frontend/react_app/src/App.js**
  - Updated all state, props, and handler logic to use arrays for all rule types.
  - Ensured panels receive arrays and access the first element.

- **frontend/react_app/src/components/EntryRulesPanel.js**
  - Refactored to expect `entryRules` (array) prop.
  - Rendered Primary Source as a `<select>` with correct `onChange` handler for `"entry_rules.0.primary_source"`.

- **frontend/react_app/src/components/StopRulesPanel.js**
  - Refactored to expect `initialStopRules` (array) prop.

- **frontend/react_app/src/components/TrailingStopRulesPanel.js**
  - Confirmed already array-based; no changes needed.

- **frontend/react_app/src/components/TakeProfitRulesPanel.js**
  - Confirmed already array-based; no changes needed.

- **frontend/react_app/src/components/TradeTable.js**
  - Updated flattening and rendering logic to use array notation for all rule types.

- **frontend/react_app/src/components/QuickEntryPanel.js**
  - Updated to use array-based access for all rule types.

- **frontend/react_app/src/utils/handleInputChange.js**
  - Updated all logic to set/read rule fields using arrays (e.g., `"entry_rules.0.primary_source"`).
  - Ensured all cases for rule fields use the array form.

---

### 3. Backend Code
- **backend/app.py**
  - Updated all trade object creation and serialization to use arrays for all rule types.

- **backend/engine/entry_evaluator.py**
  - Updated all logic to use `trade.get('entry_rules', [{}])[0]` for entry rules.

- **backend/engine/stop_loss_evaluator.py**
  - Updated all logic to use `trade.get('trailing_stop_rules', [{}])[0]` for trailing stop rules.

- **backend/engine/trailing_stop_evaluator.py**
  - Updated all logic to use `trade.get('trailing_stop_rules', [{}])[0]` for trailing stop rules.

---

### 4. Backend Tests, Demos, and Manual Files
- **All test/demo/manual files in `backend/tests/`, `backend/manual_tests/`, and root backend directory** (including but not limited to):
  - `test_validation.py`
  - `test_trade_manager.py`
  - `test_stoploss_nested.py`
  - `test_entry_evaluator.py`
  - `test_unified_rule_engine.py`
  - `test_with_stop_loss.py`
  - `test_next_stage.py`
  - `test_200_shares.py`
  - `simple_status_test.py`
  - `simple_architecture_demo.py`
  - `corrected_trade_demo.py`
  - `basic_trade_demo.py`
  - `save_trade_test.py`
  - `entry_test.py`
  - `manual_tests/test_validate_trade.py`
  - `manual_tests/test_activation_pipeline.py`
- **All test data and logic now use arrays for all rule types.**

---

## Summary of the Migration
- All references to `entry_rule`, `initial_stop_rule`, `trailing_stop_rule`, and `take_profit_rule` as objects have been removed.
- All code, config, data, and tests now use arrays for all rule types.
- All UI components, handlers, and backend logic access the first element of the array for each rule type (e.g., `entry_rules[0]`).
- The migration was full-stack: schema, config, frontend, backend, and tests.

---

**This document provides the full context and specifics of the refactor for sharing or future reference.** 