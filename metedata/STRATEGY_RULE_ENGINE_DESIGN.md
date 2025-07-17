# STRATEGY RULE ENGINE DESIGN
_Last updated: 2025-07-04_

## Project Philosophy
- All rule options (primary source, condition, secondary source) are backend-defined and validated.
- GUI provides user-friendly validation, but backend is the source of truth and always re-validates before activation.
- System is designed for extensibility, performance, and clarity—not HFT.
- All dropdowns/options are backend-driven/configurable for future growth.

## Rule Structure
- Each trade can have up to 4 rules: Entry, Initial Stop, Trailing Stop, Take Profit.
- Each rule is structured as: **Primary Source | Condition | Secondary Source | Value**
- Example rules:
  - Price >= Custom (user-defined value)
  - Price >= EMA(8) (user-defined period)
  - Price >= TradingView Alert (value set at alert time)
- Only one rule per type per trade (except for future TradingView alert flexibility).

## Indicator Handling
- User can select any integer period for indicators (e.g., EMA(8), SMA(21)).
- Backend caches recent price history for each symbol (e.g., last 200–500 bars).
- Common periods are precomputed on each tick; rare periods are computed on demand and cached.
- Performance is a priority, but occasional slight delays for rare periods are acceptable.

## TradingView Alerts
- Only one alert per trade for now.
- When alert is received, all other conditions are checked; if passed, order is executed.
- Alert value and timestamp are logged for audit/tracking.

## Portfolio Filter
- Per-trade, not global.
- Initially: must have $X available buying power (simple numeric threshold).
- User is alerted in GUI if filter blocks a trade.
- Complexity will increase over time, but always as a backend-defined list.

## Validation Workflow
- GUI validates before allowing "Activate."
- Backend re-validates on "Activate" request.
- If backend validation fails, user is notified in GUI with a clear error.
- System can never be in a state where an order is activated but cannot be evaluated.

## Logging/Audit
- Log all rule evaluations that result in an action (entry, exit, etc.), and all TradingView alerts received.
- Store logs in a simple database table (e.g., SQLite, Postgres) or structured log file (JSONL or CSV).
- Each log entry should include: timestamp, trade ID, rule type, rule details, evaluation result, and (if applicable) alert value.

## Constraints
- All dropdowns/options are backend-driven and validated.
- Only one rule per type per trade (except for future TradingView alert flexibility).
- No custom indicators as primary source (for now).
- No multiple TradingView alerts per trade (for now).
- No complex portfolio filters (beyond available buying power) at launch.

## Out of Scope (for now)
- Custom indicators as primary source.
- Multiple TradingView alerts per trade.
- Complex portfolio filters (beyond available buying power).
- Multiple rules of the same type per trade.

## Open Questions / To Be Decided
- [ ] Preferred database/storage for logs/audit (default: SQLite or JSONL file)
- [ ] Details of future portfolio filter logic
- [ ] Details of future TradingView alert expansion

## Example Rule Table
| Rule Type      | Primary Source | Condition | Secondary Source   | Value                |
|----------------|---------------|-----------|--------------------|----------------------|
| Entry          | Price         | >=        | Custom             | 100                  |
| Entry          | Price         | >=        | EMA 8              | (calculated)         |
| Entry          | Price         | >=        | TradingView alert  | (set at alert time)  |
| Initial Stop   | Price         | <=        | Custom             | 90                   |
| Trailing Stop  | Price         | <=        | EMA 21             | (calculated)         |
| Take Profit    | Price         | >=        | Custom             | 120                  |
| Portfolio      | Buying Power  | >=        | Custom             | 5000                 |

---

**This file should be updated as the project evolves. Attach or reference this file in any future AI or developer onboarding to restore project context.** 