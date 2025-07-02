📄 Trading Engine Test Documentation
✅ Overview
This document describes the current automated tests written for the trading execution engine. The tests ensure correct logic, status transitions, and validation of trade lifecycle behaviors before any code is pushed to production.

🧪 Test Coverage
1️⃣ Entry Evaluator Tests
Validate correct triggering for >= and <= conditions

Confirm fallback to entry_trigger if entry_rule_price is missing

Verify unsupported entry rules return False

Direction safety: future tests planned to dynamically check direction

✅ Test File: backend/tests/test_entry_evaluator.py

2️⃣ Stop Loss Evaluator Tests
Confirms standard stop-loss triggers

Validates trailing stops

Picks correct active stop depending on direction

Confirms correct handling when no stops are provided

✅ Test File: backend/tests/test_stop_loss_evaluator.py

3️⃣ Take Profit Evaluator Tests
Confirms take profit triggers for long trades

Confirms take profit triggers for short trades

Checks behavior when no take profit config is given

✅ Test File: backend/tests/test_take_profit_evaluator.py

4️⃣ Trade Manager Integration Test
Simulates trade activation (Active → Entry Order Submitted)

Simulates broker fill (mark_trade_filled to Live)

Validates active stop assignment after fill

Checks filled quantity and executed price recorded

Uses a mocked IB client

Verifies the test runs correctly even with the market closed

✅ Test File: backend/tests/test_trade_manager.py

⚙️ Test Frameworks & Tools
pytest for running tests

pytest-asyncio to handle async test cases

unittest.mock (MagicMock, AsyncMock) to mock dependencies

pytest tmp_path to isolate file saves without polluting real configs

🚦 Known Constraints
At least one initial stop is mandatory for all trades, enforced by validation

Trailing stops are optional

mark_trade_filled depends on correct order statuses containing "Submitted"

Current tests do not yet cover:

partial fills

short trades end-to-end

contingent exit fills

live PnL updates

These are planned for future expansion.

📌 How to Run Tests
From your project root:

bash
Copy
Edit
python -m pytest backend/tests/
or target a specific test:

bash
Copy
Edit
python -m pytest backend/tests/test_trade_manager.py
✅ All tests run independently of live market hours thanks to mocks.

🚀 Next Steps
Add short-trade scenarios

Add partial-fill scenarios

Add more robust validation tests for status transitions

Integrate into a CI/CD pipeline (e.g., GitHub Actions)

📌 Final Note
Automated tests are vital to prevent subtle status logic mismatches and regression errors, especially in a trading environment. This current suite gives a solid foundation for robust, reliable trading execution.