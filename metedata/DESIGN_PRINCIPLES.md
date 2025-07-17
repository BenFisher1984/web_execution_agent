# DESIGN PRINCIPLES
_Last updated: 2025-07-04_

## 1. **Reliability First**
- The platform must never compromise on reliability. All rule logic, validation, and execution must be deterministic and robust.
- Backend is the single source of truth for all rule options, validation, and calculations.
- No order or rule can be activated unless it is fully validated by both frontend and backend.
- All actions and rule evaluations that result in execution are logged for audit and troubleshooting.

## 2. **Backend-Driven, Strict Validation**
- All dropdown options (primary source, condition, secondary source, etc.) are defined and validated by the backend.
- The frontend only presents options that are guaranteed to be supported and valid.
- Any new complexity (e.g., new indicators, formulas like 2 x ADR) is added centrally in the backend and instantly available to all users.

## 3. **Moderate, Modular Complexity**
- The rule structure (Primary Source | Condition | Secondary Source | Value) is simple but powerful, supporting a wide range of strategies without overwhelming users.
- Only one rule per type per trade (except for future TradingView alert flexibility).
- Complexity is added incrementally, with each new feature being fully validated and tested before release.

## 4. **Performance-Conscious, Not HFT**
- The system is designed for serious retail traders, not high-frequency trading.
- Indicator calculations are cached and precomputed for common periods; rare periods are computed on demand and cached.
- The system is optimized for reliability and responsiveness, not for microsecond latency.

## 5. **User Experience and Transparency**
- The GUI provides immediate feedback and validation, preventing users from creating or activating invalid rules.
- Users are always alerted in the GUI if a rule or portfolio filter blocks a trade.
- Tooltips, documentation, and best-practice suggestions are provided for all rule options.

## 6. **Auditability and Logging**
- Every rule evaluation that results in an action (entry, exit, etc.) and every TradingView alert is logged with timestamp, trade ID, rule details, and result.
- Logs are stored in a simple, queryable format (database or structured file) for transparency and compliance.

## 7. **Extensibility and Maintainability**
- All rule options and logic are backend-configurable, allowing new features to be added without frontend rewrites.
- The codebase is modular, with clear separation between rule definition, validation, evaluation, and execution.
- Out-of-scope features (custom indicators, multiple alerts, complex portfolio logic) are explicitly documented and deferred until needed.

## 8. **Clear Boundaries and Focus**
- The platform is not intended for hedge funds or ultra-complex models, but for serious retail traders who want advanced, reliable execution tools.
- Scope creep is avoided by documenting what is out of scope and focusing on incremental, fully-tested improvements.

---

**This document should be referenced in all onboarding, code reviews, and major design decisions. Attach or paste this file to restore project philosophy and standards for any future AI or developer.** 