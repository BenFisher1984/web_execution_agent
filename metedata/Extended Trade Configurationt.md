Extended Trade Configuration Functionality Design Document
Overview
This document outlines the design decisions and implementation plan for enhancing the trade configuration system to support complex nested rules, user-customizable dropdown options, and future extensibility, ensuring a robust and maintainable architecture.

Goals
Support nested and complex trade rule objects such as trailing stops, entry rules, and take profits.

Enable user-configurable dropdown options during layout design with sensible defaults.

Provide editable parameters per rule during layout creation but enforce fixed options during trading.

Design for future extensibility, allowing optional fields for advanced features like partial take profits.

Maintain data integrity and validation using JSON Schema and coordinated frontend-backend schemas.

Ensure production-grade async lifecycle management and testing coverage.

1. Nested Trade Rule Support
Current State
Trade rules mostly represented as flat fields.

Evaluators expect flat or lightly nested dictionaries.

Enhancement
Model rule categories (entry_rule, initial_stop_rule, trailing_stop_rule, take_profit_rule) as nested JSON objects.

Example for trailing_stop_rule:

json
Copy
{
  "type": "ema",
  "length": 21,
  "offset": 0.0,
  "price_basis": "last_trade",
  "update": "tick",
  "trigger_mode": "intraday",
  "risk_amount": null
}
Update JSON Schema to validate nested objects.

Update layout config to support nested field groups.

Evaluators to safely access nested parameters.

2. User-Customizable Dropdowns and Layouts
During layout design, users can add and configure dropdown options and define which variables appear.

Dropdowns provide default options and parameters per selection.

Once layout is finalized, dropdown options and their variables become fixed for trading.

Traders interact with predefined options and editable values only.

This balances flexibility in configuration with stability in live use.

3. Common Rule Schema Structure
Each rule category shares a common core structure:

Field	Description
Primary Source	Main indicator or price source (e.g., EMA 8)
Condition	Logical operator (e.g., <=, >=)
Secondary Source	Secondary indicator or price source
Value	Numeric or custom value used in rule
Extra Params	Optional object for future extensibility

This uniformity simplifies frontend UI and backend processing.

4. Future-Proofing with Optional Fields
Add an "extra_params" optional field in each rule object to hold future enhancements (e.g., partial take profit %).

Backend and evaluators ignore extra_params unless explicitly supported.

Allows schema evolution without breaking existing data or logic.

Facilitates gradual feature rollout.

5. JSON Schema and Validation
Extend trade_schema.json to reflect nested objects and optional fields.

Use a strict JSON Schema validator in backend to:

Validate incoming trade data.

Provide meaningful error messages.

Keep schema and layout config consistent to ensure data integrity.

6. Frontend-Backend Synchronization
Frontend uses layout_config.json for form rendering and validation hints.

Backend uses JSON Schema for data validation.

Use shared schemas or code generation tools where possible.

Ensure frontend sends nested JSON matching backend expectations.

7. Production-Grade Async Architecture & Testing
Manage async lifecycle of background tasks (e.g., debounce save, sync) with explicit start() and stop() methods.

Write comprehensive unit and integration tests covering:

Schema validation.

Evaluator logic on nested data.

Async lifecycle and order workflows.

Use fixtures and mocks to isolate components during testing.

Conclusion
This design enables a flexible, extensible, and maintainable trade configuration system that meets diverse trader needs and supports evolving requirements without costly rewrites. It balances configurability during layout design with stability and reliability during trading operations.